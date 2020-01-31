#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import os
from datetime import datetime
from typing import Dict, Sequence, Union
from unittest import TestCase

from get_sources_root import get_src_root
from qf_common.config.ioc import container
from qf_lib.backtesting.alpha_model.all_tickers_used import get_all_tickers_used
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel, AlphaModelSettings
from qf_lib.backtesting.alpha_model.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.contract.contract_to_ticker_conversion.bloomberg_mapper import \
    DummyBloombergContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.execution_handler.commission_models.bps_trade_value_commission_model import \
    BpsTradeValueCommissionModel
from qf_lib.backtesting.monitoring.light_backtest_monitor import LightBacktestMonitor
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.average_true_range import average_true_range
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.futures.future_ticker import BloombergFutureTicker, FutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.data_providers.futures.futures_preset_data_provider import FuturesPresetDataProvider
from qf_lib.settings import Settings
from qf_lib.backtesting.alpha_model.futures_alpha_model_strategy import FuturesAlphaModelStrategy


class DiversifiedFuturesTradingStrategyModel(AlphaModel):
    settings = AlphaModelSettings(
        parameters=(50, 100),
        risk_estimation_factor=3
    )

    def __init__(self, fast_time_period: int, slow_time_period: int,
                 risk_estimation_factor: float, data_handler: DataHandler):
        super().__init__(risk_estimation_factor, data_handler)

        self.fast_time_period = fast_time_period
        self.slow_time_period = slow_time_period

        if fast_time_period < 3:
            raise ValueError('timeperiods shorter than 3 are pointless')
        if slow_time_period <= fast_time_period:
            raise ValueError('slow MA time period should be longer than fast MA time period')

        self.timer = self.data_handler.timer

        # Precomputed futures chains
        self.futures_data = {}  # type: Dict[Ticker, FuturesChain]

        # Precomputed prices data frames
        self.prices_data_frames = {}  # type: Dict[Ticker, PricesDataFrame]

        # Precomupted average true ranges values
        self.atr_values = {}  # type: Dict[Ticker, float]

        self.time_of_opening_position = {}  # type: Dict[Ticker, Union[datetime, None]]
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def preload_data(self, tickers: Sequence[FutureTicker]):
        self.logger.info("Preloading futures data...")

        for ticker in tickers:
            if isinstance(ticker, FutureTicker):
                num_of_bars_needed = self.slow_time_period
                current_time = self.timer.now() + RelativeDelta(hour=0, minute=0, second=0, microsecond=0)
                start_time = current_time - RelativeDelta(days=int(num_of_bars_needed * (365 / 252) + 10))

                futures_data_dict = self.data_handler.get_futures(ticker, PriceField.ohlcv(),
                                                                  start_time,
                                                                  current_time,
                                                                  Frequency.DAILY)
                self.futures_data.update(futures_data_dict)

        self.logger.info("Finished futures data preloading...")

    def _get_data(self, ticker: Ticker, start_date: datetime, end_date: datetime):
        """
        Downloads the OHCLV Prices data frame for the given ticker. In case of a FutureTicker, the function downloads
        the Futures Chain and applies backward adjustment to the prices.
        """
        if isinstance(ticker, FutureTicker):
            self.prices_data_frames[ticker] = self.futures_data[ticker].get_chain(start_date, end_date,
                                                                                  FuturesAdjustmentMethod.NTH_NEAREST)
        else:
            self.prices_data_frames[ticker] = self.data_handler.get_price(ticker, PriceField.ohlcv(), start_date,
                                                                          end_date, Frequency.DAILY)
        return self.prices_data_frames[ticker]

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure) -> Exposure:
        num_of_bars_needed = self.slow_time_period
        current_time = self.timer.now() + RelativeDelta(hour=0, minute=0, second=0, microsecond=0)

        # Compute the start time - the time range should contain at least the necessary number of bars
        # (num_of_bars_needed), but also, in cae of an open position, it should contain the data since opening the
        # position (this is further used to eventually close the position)

        start_time = current_time - RelativeDelta(days=num_of_bars_needed + 100)
        # Compute the start time, which considers the time, when the position has been open
        if current_exposure is not Exposure.OUT:
            opening_position_time = self.time_of_opening_position[ticker]
            start_time = min(start_time, opening_position_time)

        # Get the data frame containing Open, High, Low, Close prices and Volume
        data_frame = self._get_data(ticker, start_time, current_time)
        data_frame = data_frame[[PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]].dropna(how='all')

        close_tms = data_frame[PriceField.Close]

        try:
            # Compute the ATR
            fields = [PriceField.Close, PriceField.High, PriceField.Low]
            atr_df = data_frame[fields].fillna(method='pad')
            atr_df = atr_df[-num_of_bars_needed:]
            self.atr_values[ticker] = average_true_range(atr_df, normalized=True)

            ############################
            #      Opening position    #
            ############################

            current_price = close_tms.iloc[-1]

            # Shift by one day, as we always calculate the exposure on before market open
            close_tms = close_tms.fillna(method="pad")
            close_tms = close_tms.iloc[-self.slow_time_period:]

            # Compute the fast and slow simple moving averages
            fast_ma = sum(close_tms.iloc[-self.fast_time_period:]) / self.fast_time_period
            slow_ma = sum(close_tms) / self.slow_time_period

            if fast_ma > slow_ma:
                # Long entries are only allowed if the 50-day moving average is above the 100-day moving average.
                # If today’s closing price is the highest close in the past 50 days, we buy.
                highest_price = max(close_tms[-self.fast_time_period:])
                if current_price >= highest_price:
                    if current_exposure == Exposure.OUT:
                        self.time_of_opening_position[ticker] = close_tms.index[-1]
                    return Exposure.LONG
            else:
                # Short entries are only allowed if the 50-day moving average is below the 100-day moving average.
                # If today’s closing price is the lowest close in the past 50 days, we sell.
                lowest_price = min(close_tms[-self.fast_time_period:])
                if current_price <= lowest_price:
                    if current_exposure == Exposure.OUT:
                        self.time_of_opening_position[ticker] = close_tms.index[-1]
                    return Exposure.SHORT

            ############################
            #     Closing position     #
            ############################

            if current_exposure == Exposure.LONG:
                # A long position is closed when it has moved three ATR units down from its highest closing price
                # since the position was opened.

                # Get the close prices, since opening the position
                opening_position_time = self.time_of_opening_position[ticker]
                close_prices = close_tms.loc[opening_position_time:].dropna()

                if current_price < max(close_prices) * (1 - 3 * self.atr_values[ticker]):
                    return Exposure.OUT

            elif current_exposure == Exposure.SHORT:
                # A short position is closed when it has moved three ATR units up from its lowest closing price
                # since the position was opened.

                # Get the close prices, since opening the position
                opening_position_time = self.time_of_opening_position[ticker]
                close_prices = close_tms.loc[opening_position_time:].dropna()

                if current_price > min(close_prices) * (1 + 3 * self.atr_values[ticker]):
                    return Exposure.OUT

        except (KeyError, ValueError):
            # No price at this day
            pass

        return current_exposure

    def _atr_fraction_at_risk(self, ticker, time_period):
        fraction_at_risk = self.atr_values[ticker] * self.risk_estimation_factor
        return fraction_at_risk


def get_data_provider(tickers, fields, start_date, end_date, frequency=Frequency.DAILY, check_data_availability=True):
    str_to_ticker_dict = {t.family_id: t for t in tickers if isinstance(t, BloombergFutureTicker)}
    ticker_to_str_dict = {t: t.family_id for t in tickers if isinstance(t, BloombergFutureTicker)}

    def get_data():
        if bbg_provider.connected:
            future_tickers = [ticker for ticker in tickers if isinstance(ticker, BloombergFutureTicker)]
            non_future_tickers = [ticker for ticker in tickers if not isinstance(ticker, BloombergFutureTicker)]

            if len(future_tickers) > 0:
                all_future_tickers_dict = bbg_provider.get_futures_chain_tickers(future_tickers, end_date)
                all_futures_tickers = [t for tickers_chain in all_future_tickers_dict.values() for t in
                                       tickers_chain.values]

                all_tickers = all_futures_tickers + non_future_tickers
                all_future_tickers_str_dict = {
                    ticker_to_str_dict[k]: v for k, v in all_future_tickers_dict.items()
                }
            else:
                all_tickers = non_future_tickers
                all_future_tickers_str_dict = {}

            data_array = bbg_provider.get_price(all_tickers, fields, start_date, end_date, frequency)

            return data_array, all_future_tickers_str_dict

    # ----- bloomberg data provider ----- #
    settings_path = os.path.join(get_src_root(), 'qf_tests/config/test_settings.json')
    settings = Settings(settings_path)
    bbg_provider = BloombergDataProvider(settings)
    bbg_provider.connect()

    data_array, all_future_tickers_str_dict = cached_value(get_data, "Bloomberg_test_data.cache")

    # Map the strings in all_future_tickers_str_dict into future tickers
    all_future_tickers_dict = {
        str_to_ticker_dict[k]: v for k, v in all_future_tickers_str_dict.items() if k in str_to_ticker_dict.keys()
    }

    return FuturesPresetDataProvider(
        data=data_array,
        exp_dates=all_future_tickers_dict,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        check_data_availability=check_data_availability
    )


def main():
    model_type = DiversifiedFuturesTradingStrategyModel

    # Position sizing is volatility adjusted according to the ATR-based formula previously shown,
    # with a risk factor of 20 basis points.
    initial_risk = 0.03
    commission_model = BpsTradeValueCommissionModel(0.0)

    start_date = str_to_date('2000-01-01')
    end_date = str_to_date('2009-01-01')

    BeforeMarketOpenEvent.set_trigger_time({"hour": 8, "minute": 0, "second": 0, "microsecond": 0})
    MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
    MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})
    AfterMarketCloseEvent.set_trigger_time({"hour": 23, "minute": 00, "second": 0, "microsecond": 0})

    # ----- build trading session ----- #
    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_backtest_name(
        'Heating Oil, 15 days before exp date, 0.03 ATR, no comission, simple mov avg, contract size = 1')
    session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk)
    contract_ticker_mapper = DummyBloombergContractTickerMapper()
    session_builder.set_contract_ticker_mapper(contract_ticker_mapper)
    session_builder.set_commission_model(commission_model)
    session_builder.set_monitor_type(LightBacktestMonitor)
    session_builder.set_frequency(Frequency.DAILY)

    ts = session_builder.build(start_date, end_date)

    # ----- build models ----- #
    model_factory = AlphaModelFactory(ts.data_handler)
    model = model_factory.make_parametrized_model(model_type)

    tickers_universe = {
        "Non-agricultural": {
            "Heating Oil": BloombergFutureTicker("Heating Oil", "HO{} Comdty", ts.timer, ts.data_handler, 1, 15, 1),
        },
    }
    string_tickers_list = [list(x.values()) for x in tickers_universe.values()]
    model_tickers = [ticker for sublist in string_tickers_list for ticker in sublist]
    model_tickers_dict = {model: model_tickers}

    # ----- preload price data ----- #
    all_tickers_used = get_all_tickers_used(model_tickers_dict)
    data_provider = get_data_provider(all_tickers_used,
                                      PriceField.ohlcv(),
                                      start_date + RelativeDelta(year=1990, month=1, day=1),
                                      end_date)
    ts.data_handler.data_provider = data_provider
    model.preload_data(all_tickers_used)

    # ----- start trading ----- #
    strategy = FuturesAlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=False)
    ts.start_trading()

    actual_end_value = ts.portfolio.portfolio_eod_series()[-1]
    expected_value = 9838159.07

    print("Expected End Value = {}".format(expected_value))
    print("Actual End Value   = {}".format(actual_end_value))
    print("DIFF               = {}".format(expected_value - actual_end_value))

    test = TestCase()
    test.assertAlmostEqual(expected_value, actual_end_value, places=2)


if __name__ == "__main__":
    main()
