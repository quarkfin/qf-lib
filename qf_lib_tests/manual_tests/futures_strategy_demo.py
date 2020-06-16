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

from datetime import datetime
from unittest import TestCase

from qf_common.config.ioc import container
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel, AlphaModelSettings
from qf_lib.backtesting.alpha_model.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.average_true_range import average_true_range
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.backtesting.alpha_model.futures_alpha_model_strategy import FuturesAlphaModelStrategy


class SimpleFuturesModel(AlphaModel):
    settings = AlphaModelSettings(
        parameters=(50, 100),
        risk_estimation_factor=3
    )

    def __init__(self, fast_time_period: int, slow_time_period: int,
                 risk_estimation_factor: float, data_handler: DataHandler):
        super().__init__(risk_estimation_factor, data_handler)

        self.fast_time_period = fast_time_period
        self.slow_time_period = slow_time_period

        self.timer = self.data_handler.timer

        self.futures_chain = None  # type: FuturesChain
        self.time_of_opening_position = None  # type: datetime
        self.average_true_range = None  # type: float

    def calculate_exposure(self, ticker: FutureTicker, current_exposure: Exposure) -> Exposure:
        num_of_bars_needed = self.slow_time_period
        current_time = self.timer.now()

        # Compute the start time
        start_time = current_time - RelativeDelta(days=num_of_bars_needed + 100)

        if self.futures_chain is None:
            # Create Futures Chain object
            self.futures_chain = FuturesChain(ticker, self.data_handler)

        # Get the data frame containing High, Low, Close prices
        data_frame = self.futures_chain.get_price([PriceField.High, PriceField.Low, PriceField.Close], start_time,
                                                  current_time)
        data_frame = data_frame.dropna(how='all').fillna(method='pad')

        close_tms = data_frame[PriceField.Close]
        close_tms = close_tms.iloc[-self.slow_time_period:]

        try:
            # Compute the ATR
            atr_df = data_frame[-num_of_bars_needed:]
            self.average_true_range = average_true_range(atr_df, normalized=True)

            ############################
            #      Opening position    #
            ############################

            current_price = close_tms.iloc[-1]

            # Compute the fast and slow simple moving averages
            fast_ma = sum(close_tms.iloc[-self.fast_time_period:]) / self.fast_time_period
            slow_ma = sum(close_tms) / self.slow_time_period

            if fast_ma > slow_ma:
                # Long entries are only allowed if the fast moving average is above the slow moving average.
                # If today’s closing price is the highest close in the past 50 days, we buy.
                highest_price = max(close_tms[-self.fast_time_period:])
                if current_price >= highest_price:
                    if current_exposure == Exposure.OUT:
                        self.time_of_opening_position = close_tms.index[-1]
                    return Exposure.LONG
            else:
                # Short entries are only allowed if the fast moving average is below the slow moving average.
                # If today’s closing price is the lowest close in the past 50 days, we sell.
                lowest_price = min(close_tms[-self.fast_time_period:])
                if current_price <= lowest_price:
                    if current_exposure == Exposure.OUT:
                        self.time_of_opening_position = close_tms.index[-1]
                    return Exposure.SHORT

            ############################
            #     Closing position     #
            ############################

            if current_exposure == Exposure.LONG:
                # A long position is closed when it has moved three ATR units down from its highest closing price
                # since the position was opened.
                close_prices = close_tms.loc[self.time_of_opening_position:].dropna()
                if current_price < max(close_prices) * (1 - 3 * self.average_true_range):
                    return Exposure.OUT

            elif current_exposure == Exposure.SHORT:
                # A short position is closed when it has moved three ATR units up from its lowest closing price
                # since the position was opened.
                close_prices = close_tms.loc[self.time_of_opening_position:].dropna()
                if current_price > min(close_prices) * (1 + 3 * self.average_true_range):
                    return Exposure.OUT

        except (KeyError, ValueError):
            # No price at this day
            pass

        return current_exposure

    def _atr_fraction_at_risk(self, ticker, time_period):
        fraction_at_risk = self.average_true_range * self.risk_estimation_factor
        return fraction_at_risk


def main():
    start_date = str_to_date('2003-05-30')
    end_date = str_to_date('2009-01-01')

    model_tickers = [BloombergFutureTicker("Corn", "C {} Comdty", 1, 10, 1)]
    initial_risk = 0.006

    # ----- build trading session ----- #
    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_backtest_name('Simple Futures Strategy')
    session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk)
    session_builder.set_frequency(Frequency.DAILY)

    ts = session_builder.build(start_date, end_date)

    # ----- build models ----- #
    model_type = SimpleFuturesModel
    model_factory = AlphaModelFactory(ts.data_handler)
    model = model_factory.make_parametrized_model(model_type)
    model_tickers_dict = {model: model_tickers}

    # ----- start trading ----- #
    ts.use_data_preloading(model_tickers)

    FuturesAlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=False)
    ts.start_trading()

    actual_end_value = ts.portfolio.portfolio_eod_series()[-1]
    expected_value = 10317477.750000006

    print("Expected End Value = {}".format(expected_value))
    print("Actual End Value   = {}".format(actual_end_value))
    print("DIFF               = {}".format(expected_value - actual_end_value))

    test = TestCase()
    test.assertAlmostEqual(expected_value, actual_end_value, places=2)


if __name__ == "__main__":
    main()
