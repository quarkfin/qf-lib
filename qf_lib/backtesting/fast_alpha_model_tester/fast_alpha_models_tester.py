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
import traceback
from datetime import datetime
from itertools import count
from typing import Sequence, Type, List, Union, Dict, Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.fast_alpha_model_tester.backtest_summary import BacktestSummary, BacktestSummaryElement
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer, Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.dimension_names import TICKERS
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import cast_data_array_to_proper_type, tickers_dict_to_data_array
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class FastAlphaModelTesterConfig:
    """
    Parameters
    ----------
    model_type: type[AlphaModel]
        type of the alpha model that needs to be tested
    kwargs:
        all arguments that should be passed to the init function of the alpha model (may contain data_provider but
        it will be overwritten, when initializing the model)
    tested_params: Union[str, Sequence[str]]
        strings, representing the init parameters of AlphaModel that are being verified in the test. The kwargs dict
        needs to contain them.
    """

    def __init__(self, model_type: Type[AlphaModel], kwargs: Dict[str, Any], tested_params: Union[str, Sequence[str]]):
        self.model_type = model_type  # type: Type[AlphaModel]
        self.kwargs = kwargs
        self.tested_parameters_names, _ = convert_to_list(tested_params, str)

        assert set(param for param in self.tested_parameters_names if param in self.kwargs.keys()) == set(
            self.tested_parameters_names), "The tested_params need to be passed in the kwargs"

    def generate_model(self, data_provider: DataProvider):
        return self.model_type(**self.kwargs, data_provider=data_provider)

    def model_parameters(self):
        return tuple(self.kwargs[param] for param in self.tested_parameters_names)


class FastAlphaModelTester:
    """
    ModelTester in which portfolio construction is simulated by always following the suggested Exposures from
    AlphaModels. All Tickers are traded with same weights (weights are constant across time and equal to 1 / N
    where N is number of assets).
    """

    def __init__(self, alpha_model_configs: Sequence[FastAlphaModelTesterConfig],
                 tickers: Sequence[Ticker], start_date: datetime, end_date: datetime,
                 data_provider: DataProvider, timer: Timer = None, n_jobs: int = 1,
                 frequency: Frequency = Frequency.DAILY, start_time: Dict = None, end_time: Dict = None,
                 close_position_at_the_end_of_day: bool = False):
        """
        Parameters
        ----------
        alpha_model_configs: Sequence[FastAlphaModelTesterConfig]
            configs, each of which defines the parameters to be tested
        tickers: Sequence[Ticker]
            tickers to be tested
        start_date: datetime
            start date of the backtest
        end_date: datetime
            end date of the backtest
        data_provider: DataProvider
        timer: Timer
            timer in case it is needed.
            Often you need to have a timer inside your AlphaModel and the exat same timer can be passed here
            so that your AlphaModel knows the time
        n_jobs: int
            number of jobs/cores to be employed for the simmulation
        frequency: Frequency
            frequency on which the signals are generated
        start_time: Dict
            it is only used when the frequency is higher than daily, and has to be provided in that case.
            example: {"hour": 9, "minute": 30}
            Means that the signal generation will start at 9:30 every day
            only hour and minute will be used. seconds and microseconds will not be used.
        end_time: Dict
            it is only used when the frequency is higher than daily, and has to be provided in that case.
            example: {"hour": 16, "minute": 00}
            Means that the signal generation will end at 16:00 every day
            only hour and minute will be used. second and microsecond will not be used.
        close_position_at_the_end_of_day: bool
            it is only used when the frequency is higher than daily
            If True, the last signal of the day will always be set to close the existing position.
            This is to avoid overnight exposure.
            If False (default), position might be carried overnight, and will not be forced to be closed.
        """
        self.timer = timer
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self._alpha_model_configs = alpha_model_configs
        self._tickers = self._get_valid_tickers(tickers)
        self._start_date = start_date
        self._end_date = end_date
        self._data_provider = data_provider
        self._timer = SettableTimer(start_date) if timer is None else timer
        self._n_jobs = n_jobs
        self._frequency = frequency
        self._start_time = start_time
        self._end_time = end_time
        self._close_position_at_the_end_of_day = close_position_at_the_end_of_day

        # use 1min data frequency for data if signal generation is intra-day.
        # use Daily frequency for any other time frame
        self._data_frequency = Frequency.MIN_1 if self._frequency > Frequency.DAILY else Frequency.DAILY

        assert len(set(config.model_type for config in alpha_model_configs)) == 1, \
            "All passed FastAlphaModelTesterConfig should have the same alpha model type"
        self._model_type = alpha_model_configs[0].model_type

        if self._frequency > Frequency.DAILY:
            assert self._start_time is not None, "Start time cannot be none for frequency higher than daily"
            assert self._end_time is not None, "End time cannot be none for frequency higher than daily"
            # add zeroed second ad microseconds to create clean bars
            self._start_time["second"] = 0
            self._start_time["microsecond"] = 0
            self._end_time["second"] = 0
            self._end_time["microsecond"] = 0
        else:
            if self._start_time is not None or self._end_time is not None:
                self.logger.warning("Start time and end time will be ignored for frequency lower than daily")

    def test_alpha_models(self) -> BacktestSummary:
        self.logger.info("{} parameters sets to be tested".format(len(self._alpha_model_configs)))

        prices_data_array = self._get_data_for_backtest()
        exposure_values_df_list = self._generate_exposures_for_all_params_sets()
        backtest_summary_elem_list = self._calculate_backtest_summary_elements(exposure_values_df_list,
                                                                               prices_data_array)
        backtest_summary = BacktestSummary(self._tickers, self._model_type, backtest_summary_elem_list,
                                           self._start_date, self._end_date)
        return backtest_summary

    def _get_valid_tickers(self, original_ticker: Sequence[Ticker]) -> List[Ticker]:
        tickers = []
        for ticker in original_ticker:
            try:
                if isinstance(ticker, FutureTicker):
                    ticker.initialize_data_provider(self._timer, self._data_provider)
                    ticker = ticker.get_current_specific_ticker()
                tickers.append(ticker)
            except NoValidTickerException:
                self.logger.warning("No valid ticker for {}".format(ticker.name))

        return tickers

    def _get_data_for_backtest(self) -> QFDataArray:
        """
        Creates a QFDataArray containing OHLCV values for all tickers passes to Fast Alpha Models Tester.
        """
        self.logger.info("\nLoading all price values of tickers:")
        self._timer.set_current_time(self._end_date)
        tickers_dict = {}

        for ticker in self._tickers:
            if isinstance(ticker, FutureTicker):
                fc = FuturesChain(ticker, self._data_provider)
                tickers_dict[ticker] = fc.get_price(PriceField.ohlcv(), self._start_date, self._end_date,
                                                    self._data_frequency)
            else:
                tickers_dict[ticker] = self._data_provider.get_price(ticker, PriceField.ohlcv(), self._start_date,
                                                                     self._end_date, self._data_frequency)

        prices_data_array = tickers_dict_to_data_array(tickers_dict, self._tickers, PriceField.ohlcv())
        return prices_data_array

    def _generate_exposures_for_all_params_sets(self) -> List[QFDataFrame]:
        self.logger.info("\nGenerating exposures:")
        exposure_values_df_list = Parallel(n_jobs=self._n_jobs)(delayed(self._generate_exposure_values)
                                                                (config, self._data_provider, self._tickers)
                                                                for config in self._alpha_model_configs)
        print("\nFinished generation of exposures.")
        return exposure_values_df_list

    def _calculate_backtest_summary_elements(self, exposure_values_df_list: List[QFDataFrame],
                                             prices_data_array: QFDataArray) -> List[BacktestSummaryElement]:

        open_prices_df = self._get_open_prices(prices_data_array)
        open_to_open_returns_df = open_prices_df.to_simple_returns()

        self.logger.info("\nGenerating backtest summaries:")
        # Consider each ticker separately and all tickers altogether
        tickers_for_summary = [[ticker] for ticker in self._tickers]
        if len(self._tickers) > 1:
            tickers_for_summary += [self._tickers]

        all_params = [(config, exposure_values_df, tickers)
                      for config, exposure_values_df in zip(self._alpha_model_configs, exposure_values_df_list)
                      for tickers in tickers_for_summary]

        backtest_summary_elem_list = Parallel(n_jobs=self._n_jobs)(
            delayed(self._calculate_backtest_summary)(tickers, config, prices_data_array,
                                                      open_to_open_returns_df[tickers],
                                                      exposure_values_df[tickers])
            for config, exposure_values_df, tickers in all_params
        )

        return backtest_summary_elem_list

    def _get_open_prices(self, prices_data_array: QFDataArray) -> PricesDataFrame:
        """ Returns PricesDataFrame consisting of only Open prices. """
        open_prices_df = cast_data_array_to_proper_type(prices_data_array.loc[:, :, PriceField.Open],
                                                        use_prices_types=True).dropna(how="all")
        return open_prices_df

    def _calculate_backtest_summary(self, tickers: Union[Ticker, Sequence[Ticker]], config: FastAlphaModelTesterConfig,
                                    prices_data_array: QFDataArray,
                                    open_to_open_returns_df: QFDataFrame,
                                    exposure_values_df: QFDataFrame) -> BacktestSummaryElement:

        portfolio_rets_tms = self._calculate_portfolio_returns_tms(open_to_open_returns_df, exposure_values_df)
        trades = self._calculate_trades(prices_data_array, exposure_values_df)
        tickers, _ = convert_to_list(tickers, Ticker)

        element = BacktestSummaryElement(config.model_parameters(), config.tested_parameters_names, portfolio_rets_tms,
                                         trades, tickers)
        return element

    def _calculate_portfolio_returns_tms(self, open_to_open_returns_df: QFDataFrame,
                                         exposure_values_df: QFDataFrame) \
            -> SimpleReturnsSeries:
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

        if self._frequency <= Frequency.DAILY:
            union_index = open_to_open_returns_df.index.union(exposure_values_df.index)
            exposure_values_df_expanded = exposure_values_df.reindex(union_index, method="ffill")
            exposure_values_df_expanded = exposure_values_df_expanded.shift(2, axis=0)

            open_to_open_returns_df_expanded = open_to_open_returns_df.reindex(union_index)
            open_to_open_returns_df_expanded = open_to_open_returns_df_expanded.fillna(0)

            returns_of_strategies_df = exposure_values_df_expanded * open_to_open_returns_df_expanded
        else:
            # Assume that we implement the signal with the lag of 1min. Requires shifting returns  by 2min.
            lag = pd.Timedelta(minutes=2)
            shifted_exposure_df = QFDataFrame(data=exposure_values_df.values,
                                              index=exposure_values_df.index + lag,
                                              columns=exposure_values_df.columns)
            union_index = open_to_open_returns_df.index.union(shifted_exposure_df.index)
            shifted_exposure_df = shifted_exposure_df.reindex(union_index, method="ffill")

            open_to_open_returns_df_expanded = open_to_open_returns_df.reindex(union_index)
            open_to_open_returns_df_expanded = open_to_open_returns_df_expanded.fillna(0)
            returns_of_strategies_df = open_to_open_returns_df_expanded * shifted_exposure_df

        returns_of_strategies_df = returns_of_strategies_df.dropna(axis=0, how='all')
        returns_of_strategies_df = cast_dataframe(returns_of_strategies_df, SimpleReturnsDataFrame)

        weights = Portfolio.one_over_n_weights(open_to_open_returns_df.columns)
        portfolio_rets_tms, _ = Portfolio.constant_weights(returns_of_strategies_df, weights)

        return portfolio_rets_tms

    def _calculate_trades(self, prices_array: QFDataArray, exposure_df: QFDataFrame) -> List[Trade]:

        if self._frequency > Frequency.DAILY:
            lag = pd.Timedelta(minutes=1)
        else:
            lag = pd.Timedelta(days=1)

        shifted_exposure_df = QFDataFrame(data=exposure_df.values, index=exposure_df.index + lag,
                                          columns=exposure_df.columns)

        trade_data_list = []
        for ticker, exposures_tms in shifted_exposure_df.iteritems():
            trade_data_partial_list = self.generate_trades_for_ticker(prices_array, exposures_tms, ticker)
            trade_data_list.extend(trade_data_partial_list)

        return trade_data_list

    def generate_trades_for_ticker(self, prices_array: QFDataArray, exposures_tms: pd.Series, ticker: Ticker) \
            -> List[Trade]:

        open_prices_tms = cast_data_array_to_proper_type(prices_array.loc[:, ticker, PriceField.Open],
                                                         use_prices_types=True)

        union_index = open_prices_tms.index.union(exposures_tms.index)
        open_prices_tms = open_prices_tms.reindex(union_index, method="ffill")
        open_prices_tms = open_prices_tms[exposures_tms.index]

        # historical data cropped to the time frame of the backtest (from start date till end date)
        historical_data = pd.concat((exposures_tms, open_prices_tms), axis=1).loc[self._start_date:]

        prev_exposure = 0.0
        trades_list = []

        trade_start_date = None
        trade_exposure = None
        trade_start_price = None

        # If the first exposure is nan - skip it
        first_exposure = historical_data.iloc[0, 0]
        if np.isnan(first_exposure):
            historical_data = historical_data.iloc[1:]

        for curr_date, row in historical_data.iterrows():
            curr_date = curr_date.to_pydatetime()
            curr_exposure, curr_price = row.values

            # skipping the nan Open prices
            if np.isnan(curr_price):
                self.logger.warning("Open price is None, cannot create trade on {} for {}".format(
                    curr_date, str(ticker)))
                continue

            out_of_the_market = trade_exposure is None
            if out_of_the_market:
                assert prev_exposure == 0.0

                if curr_exposure != 0.0:
                    trade_start_date = curr_date
                    trade_exposure = curr_exposure
                    trade_start_price = curr_price
            else:
                assert prev_exposure != 0.0

                exposure_change = int(curr_exposure - prev_exposure)
                should_close_position = exposure_change != 0.0

                if should_close_position:
                    trades_list.append(Trade(
                        start_time=trade_start_date,
                        end_time=curr_date,
                        ticker=ticker,
                        pnl=(curr_price / trade_start_price - 1) * trade_exposure,
                        commission=0.0,
                        direction=int(trade_exposure)
                    ))
                    trade_start_date = None
                    trade_exposure = None
                    trade_start_price = None

                    going_into_opposite_direction = curr_exposure != 0.0
                    if going_into_opposite_direction:
                        trade_start_date = curr_date
                        trade_exposure = curr_exposure
                        trade_start_price = curr_price

            prev_exposure = curr_exposure

        return trades_list

    def _generate_exposure_values(self, config: FastAlphaModelTesterConfig, data_provider: DataProvider,
                                  tickers: Sequence[Ticker]):
        """
        For the given Alpha model and its parameters, generates the dataframe containing all exposure values, that
        will be returned by the model through signals.
        In case of an exception or error in the processing Exposure.OUT is returned.
        """

        model = config.generate_model(data_provider)

        current_exposures_values = QFSeries(index=pd.Index(tickers, name=TICKERS))
        current_exposures_values[:] = 0.0

        backtest_dates = self._get_backtest_dates()

        exposure_values_df = QFDataFrame(
            index=backtest_dates.index,
            columns=pd.Index(tickers, name=TICKERS)
        )

        for ticker in tickers:
            if isinstance(ticker, FutureTicker):
                # Even if the tickers were already initialized, during pickling process, the data provider and timer
                # information is lost
                ticker.initialize_data_provider(self._timer, data_provider)

        for i, curr_datetime in enumerate(backtest_dates.index):
            if i % 1000 == 0:
                self.logger.info('{} / {} of Exposure dates processed'.format(i, len(backtest_dates)))

            new_exposures = QFSeries(index=tickers)
            self._timer.set_current_time(curr_datetime)

            for j, ticker, curr_exp_value in zip(count(), tickers, current_exposures_values):
                curr_exp = Exposure(curr_exp_value) if is_finite_number(curr_exp_value) else Exposure.OUT
                try:
                    new_exp = model.calculate_exposure(ticker, curr_exp, curr_datetime, self._data_frequency)
                except Exception as ex:
                    self.logger.warning(f"Exception {ex} for exposure calculations {curr_datetime}, {ticker}")
                    self.logger.warning(traceback.format_exc())

                    new_exp = Exposure.OUT
                new_exposures.iloc[j] = new_exp.value if new_exp is not None else Exposure.OUT

            # assuming that we always follow the new_exposures from strategy, disregarding confidence levels
            # and expected moves, looking only at the suggested exposure
            current_exposures_values = new_exposures
            exposure_values_df.iloc[i, :] = current_exposures_values

        if self._close_position_at_the_end_of_day:
            exposure_out = backtest_dates[backtest_dates == 1]
            exposure_values_df.loc[exposure_out.index, :] = Exposure.OUT.value

        exposure_values_df = exposure_values_df.dropna(axis=1, how="all")
        return exposure_values_df

    def _get_backtest_dates(self) -> QFSeries:
        """
        Returns series indexed by all dates that will be used for signal generation.
        Value of series == 1  it means that we need to close the position at the end of the day
        """
        if self._frequency == Frequency.DAILY:
            backtest_dates = pd.date_range(self._start_date, self._end_date, freq="D")
            backtest_dates = QFSeries(backtest_dates.to_series())
            backtest_dates[:] = 0
        elif self._frequency > Frequency.DAILY:
            days_dates = pd.date_range(self._start_date, self._end_date, freq="D")
            signal_time_holder = []
            for day in days_dates:
                start_time = day + RelativeDelta(**self._start_time)
                end_time = day + RelativeDelta(**self._end_time)
                signal_times_for_a_day = pd.date_range(start_time, end_time, freq=self._frequency.to_pandas_freq())
                signal_times_for_a_day = QFSeries(signal_times_for_a_day.to_series())
                signal_times_for_a_day[:] = 0

                if self._close_position_at_the_end_of_day:
                    # add additional stamp or override existing with info to close the position
                    signal_times_for_a_day[end_time] = 1

                signal_time_holder.append(signal_times_for_a_day)

            backtest_dates = pd.concat(signal_time_holder)
        return backtest_dates
