from datetime import datetime
from itertools import count
from time import time
from typing import Sequence, Tuple, Type

import numpy as np
import pandas as pd
from pandas import DataFrame

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_models_testers.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.alpha_models_testers.backtest_summary import BacktestSummary, \
    BacktestSummaryElement
from qf_lib.backtesting.alpha_models_testers.fast_data_handler import FastDataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.dimension_names import TICKERS
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class FastAlphaModelTester(object):
    """
    ModelTester in which portfolio construction is simulated by always following the suggested Exposures from
    AlphaModels. All Tickers are traded with same weights (weights are constant across time).
    """

    def __init__(self, model_type: Type[AlphaModel], parameter_sets: Sequence[Tuple],
                 tickers: Sequence[Ticker], start_date: datetime, end_date: datetime,
                 data_handler: FastDataHandler, timer: SettableTimer, alpha_model_factory: AlphaModelFactory):
        self._tickers = tickers
        self._start_date = start_date
        self._end_date = end_date

        self._model_type = model_type
        self._parameter_sets = parameter_sets
        self._data_handler = data_handler
        self._timer = timer
        self._alpha_model_factory = alpha_model_factory

        self.logger = qf_logger.getChild(self.__class__.__name__)
        if type(self._data_handler) is not FastDataHandler:
            self.logger.warning("You are using a deprecated type of DataHandler. In FastAlphaModelsTester "
                                "use of FastDataHandler is suggested.")

    def test_alpha_models(self) -> BacktestSummary:
        nr_of_param_sets = len(self._parameter_sets)
        print("{} parameters sets to be tested".format(nr_of_param_sets))
        prices_data_array = self._get_data_for_backtest()

        backtest_dates = prices_data_array.dates.to_index()

        exposure_values_df_list = self._generate_exposures_for_all_params_sets(
            self._alpha_model_factory, backtest_dates, nr_of_param_sets
        )
        backtest_summary_elem_list = self._calculate_backtest_summary_elements(
            exposure_values_df_list, nr_of_param_sets, prices_data_array
        )
        backtest_summary = BacktestSummary(self._tickers, self._model_type, backtest_summary_elem_list,
                                           self._start_date, self._end_date)
        return backtest_summary

    def _get_data_for_backtest(self):
        self._timer.set_current_time(self._end_date)
        prices_data_array = self._data_handler.get_price(self._tickers, PriceField.ohlcv(), self._start_date,
                                                         self._end_date)
        return prices_data_array

    def _generate_exposures_for_all_params_sets(self, alpha_model_factory, backtest_dates, nr_of_param_sets):
        exposure_values_df_list = []
        print("Generating exposures:")
        param_set_ctr = 1

        for param_set in self._parameter_sets:
            start_time = time()
            model = alpha_model_factory.make_model(self._model_type, *param_set)
            exposure_values_df = self._generate_exposure_values(model, backtest_dates)
            exposure_values_df_list.append(exposure_values_df)
            end_time = time()

            print("{} / {} parameters sets tested".format(param_set_ctr, nr_of_param_sets))
            print("iteration time = {:5.2f} minutes".format((end_time - start_time) / 60))
            param_set_ctr += 1

        return exposure_values_df_list

    def _calculate_backtest_summary_elements(self, exposure_values_df_list, nr_of_param_sets, prices_data_array):
        open_prices_df = self._get_open_prices(prices_data_array)
        open_to_open_returns_df = open_prices_df.to_simple_returns()
        backtest_summary_elem_list = []
        print("Generating backtest summaries:")
        param_set_ctr = 1

        for param_set, exposure_values_df in zip(self._parameter_sets, exposure_values_df_list):
            start_time = time()
            backtest_summary_elem = self._calculate_backtest_summary(param_set, prices_data_array,
                                                                     open_to_open_returns_df, exposure_values_df)
            backtest_summary_elem_list.append(backtest_summary_elem)

            end_time = time()
            print("{} / {} parameters sets tested".format(param_set_ctr, nr_of_param_sets))
            print("iteration time = {:5.2f} minutes".format((end_time - start_time) / 60))
            param_set_ctr += 1

        return backtest_summary_elem_list

    def _get_open_prices(self, prices_data_array):
        open_prices_pandas_df = prices_data_array.loc[:, :, PriceField.Open].to_pandas()
        open_prices_df = cast_dataframe(open_prices_pandas_df, PricesDataFrame)
        return open_prices_df

    def _calculate_backtest_summary(self, param_set, prices_data_array, open_to_open_returns_df, exposure_values_df):
        portfolio_rets_tms = self._calculate_portfolio_returns_tms(open_to_open_returns_df, exposure_values_df)
        trades_df = self._calculate_trades(prices_data_array, exposure_values_df)

        backtest_summary = BacktestSummaryElement(param_set, portfolio_rets_tms, trades_df)

        return backtest_summary

    def _generate_exposure_values(self, model: AlphaModel, backtest_dates):
        current_exposures_values = pd.Series(index=pd.Index(self._tickers, name=TICKERS))
        current_exposures_values[:] = 0.0

        exposure_values_df = DataFrame(
            index=backtest_dates,
            columns=pd.Index(self._tickers, name=TICKERS)
        )

        for i, curr_datetime in enumerate(backtest_dates):
            new_exposures = pd.Series(index=self._tickers)
            self._timer.set_current_time(curr_datetime)

            for j, ticker, curr_exp_value in zip(count(), self._tickers, current_exposures_values):
                curr_exp = Exposure(curr_exp_value)
                new_exp = model.calculate_exposure(ticker, curr_exp)
                new_exposures.iloc[j] = new_exp.value

            # assuming that we always follow the new_exposures from strategy, disregarding confidence levels
            # and expected moves, looking only at the suggested exposure
            current_exposures_values = new_exposures
            exposure_values_df.iloc[i, :] = current_exposures_values.iloc[:]

        return exposure_values_df

    def _calculate_portfolio_returns_tms(self, open_to_open_returns_df, exposure_values_df):
        """
        SimpleReturnsSeries of the portfolio - for each date equal to the portfolio performance over the last
        open-to-open period, ex. value indexed as 2010-02-15 would refer to the portfolio value change between
        open at 14th and open at 15th, and would be based on the signal from 2010-02-13;

        the first index of the series is the Day 3 of the backtest, as the first signal calculation occurs
        after Day 1 (see ORDER OF ACTIONS below)
        the last index of the series is test_end_date and the portfolio exposure is being set to zero
        on the opening of the test_end_date

        ORDER OF ACTIONS:

        -- Day 1 --
        signal is generated, based on the historic data INCLUDING prices from Day 1
        suggested exposure for Day 2 is calculated

        -- Day 2 --
        a trade is entered, held or exited (or nothing happens) regarding the suggested exposure
        this action is performed on the opening of the day

        -- Day 3 --
        at the opening the open-to-open return is calculated
        now it is possible to estimate current portfolio value
        the simple return of the portfolio (Day 3 to Day 2) is saved and indexed with Day 3 date
        """
        shifted_signals_df = exposure_values_df.shift(2, axis=0)
        shifted_signals_df = shifted_signals_df.iloc[2:]

        daily_returns_of_strategies_df = shifted_signals_df * open_to_open_returns_df
        daily_returns_of_strategies_df = daily_returns_of_strategies_df.dropna(axis=0, how='all')

        daily_returns_of_strategies_df = cast_dataframe(
            daily_returns_of_strategies_df, SimpleReturnsDataFrame
        )  # type: SimpleReturnsDataFrame

        weights = Portfolio.one_over_n_weights(self._tickers)
        # for strategies based on more than one ticker (ex. VolLongShort) use the line below:
        # weights = pd.Series(np.ones(daily_returns_of_strategies_df.num_of_columns))

        portfolio_rets_tms, _ = Portfolio.constant_weights(daily_returns_of_strategies_df, weights)

        return portfolio_rets_tms

    def _calculate_trades(self, prices_array, exposures_df) -> pd.DataFrame:
        all_trade_fields = [
            TradeField.Ticker, TradeField.StartDate, TradeField.EndDate,
            TradeField.Open, TradeField.MaxGain, TradeField.MaxLoss, TradeField.Close, TradeField.Return,
            TradeField.Exposure
        ]

        trade_data_list = []
        shifted_signals_df = exposures_df.shift(1, axis=0)

        for ticker, exposures_tms in shifted_signals_df.iteritems():
            trade_data_partial_list = self.generate_trades_for_ticker(prices_array, exposures_tms, ticker)
            trade_data_list += trade_data_partial_list

        result = self._trade_data_to_df(all_trade_fields, trade_data_list)

        return result

    def generate_trades_for_ticker(self, prices_array, exposures_tms, ticker):
        historical_data = self._get_historical_data(exposures_tms, prices_array, ticker)

        prev_exposure = 0.0
        trades_data_list = []
        trade_data = None

        # historical data cropped to the time frame of the backtest (from start date till end date)
        cropped_historical_data = historical_data.loc[self._start_date:, :]
        for _, row in cropped_historical_data.iterrows():
            curr_exposure, curr_price, low_price, high_price = row.values
            curr_date = row.name.to_pydatetime()

            # skipping the nan exposures (the first one is sure to be nan)
            if np.isnan(curr_exposure):
                continue

            out_of_the_market = trade_data is None
            if out_of_the_market:
                assert prev_exposure == 0.0

                if curr_exposure != 0.0:
                    trade_data = _TradeData.enter_trade(ticker, curr_date, curr_price, curr_exposure, high_price,
                                                        low_price)
            else:
                assert prev_exposure != 0.0

                exposure_change = int(curr_exposure - prev_exposure)
                should_close_position = exposure_change != 0.0

                if should_close_position:
                    trade_data.exit_trade(curr_date, curr_price)
                    trades_data_list.append(trade_data)
                    trade_data = None

                    going_into_opposite_direction = curr_exposure != 0.0
                    if going_into_opposite_direction:
                        trade_data = _TradeData.enter_trade(
                            ticker, curr_date, curr_price, curr_exposure, high_price, low_price
                        )
                else:
                    trade_data.update_high_and_low(high_price, low_price)

            prev_exposure = curr_exposure

        return trades_data_list

    def _trade_data_to_df(self, all_trade_fields, trade_data_list):
        row_data_list = []

        for tr in trade_data_list:
            row_data = (
                tr.ticker, tr.start_date, tr.end_date, tr.open_price, tr.max_gain, tr.max_loss, tr.close_price,
                tr.trade_return, tr.exposure_value
            )
            row_data_list.append(row_data)

        result = pd.DataFrame(columns=pd.Index(all_trade_fields), data=row_data_list)

        return result

    def _get_historical_data(self, exposures_tms, prices_array, ticker):
        prices_df = prices_array.loc[:, ticker, :].to_pandas()
        prices_df = cast_dataframe(prices_df, PricesDataFrame)
        open_prices_tms = prices_df.loc[:, PriceField.Open]
        low_prices_tms = prices_df.loc[:, PriceField.Low]
        high_prices_tms = prices_df.loc[:, PriceField.High]
        historical_data = pd.concat((exposures_tms, open_prices_tms, low_prices_tms, high_prices_tms), axis=1)

        return historical_data


class _TradeData(object):
    def __init__(self):
        self.ticker = None
        self.start_date = None
        self.end_date = None
        self.open_price = np.nan
        self.close_price = np.nan
        self.exposure_value = np.nan

        self._highest_high_price = np.nan
        self._lowest_low_price = np.nan

    @classmethod
    def enter_trade(cls, ticker: Ticker, start_date: datetime, open_price: float, exposure: float, high_price: float,
                    low_price: float):
        trade = _TradeData()

        trade.ticker = ticker
        trade.exposure_value = exposure
        trade.start_date = start_date
        trade.open_price = open_price
        trade._highest_high_price = high_price
        trade._lowest_low_price = low_price

        return trade

    def exit_trade(self, end_date: datetime, close_price: float):
        self.end_date = end_date
        self.close_price = close_price

    def update_high_and_low(self, high_price: float, low_price: float):
        self._highest_high_price = max(high_price, self._highest_high_price)
        self._lowest_low_price = min(low_price, self._lowest_low_price)

    @property
    def max_gain(self) -> float:
        if self.exposure_value == 1.0:
            max_gain = self._highest_high_price - self.open_price
        else:  # exposure == -1.0
            max_gain = self.open_price - self._lowest_low_price

        return max_gain

    @property
    def max_loss(self):
        if self.exposure_value == 1.0:
            max_loss = self._lowest_low_price - self.open_price
        else:  # exposure == -1.0
            max_loss = self.open_price - self._highest_high_price

        return max_loss

    @property
    def trade_return(self):
        return (self.close_price / self.open_price - 1) * self.exposure_value
