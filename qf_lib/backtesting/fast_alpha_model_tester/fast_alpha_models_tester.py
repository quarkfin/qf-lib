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
import sys
from datetime import datetime
from itertools import count
from typing import Sequence, Type, List, Union, Dict, Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.fast_alpha_model_tester.backtest_summary import BacktestSummary, BacktestSummaryElement
from qf_lib.backtesting.fast_alpha_model_tester.fast_data_handler import FastDataHandler
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import SettableTimer
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
from qf_lib.data_providers.helpers import cast_data_array_to_proper_type, tickers_dict_to_data_array
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class FastAlphaModelTesterConfig:
    """
    Parameters
    ----------
    model_type: type[AlphaModel]
        type of the alpha model that needs to be tested
    kwargs:
        all arguments that should be passed to the init function of the alpha model (may contain data_handler but
        it will be overwritten, when initializing the model)
    modeled_params: Union[str, Sequence[str]]
        strings, representing the init parameters of AlphaModel that are being verified in the test. The kwargs dict
        needs to contain them.
    """

    def __init__(self, model_type: Type[AlphaModel], kwargs: Dict[str, Any], modeled_params: Union[str, Sequence[str]]):
        self.model_type = model_type  # type: Type[AlphaModel]
        self.kwargs = kwargs
        self.model_parameters_names, _ = convert_to_list(modeled_params, str)

        assert set(param for param in self.model_parameters_names if param in self.kwargs.keys()) == set(
            self.model_parameters_names), "The modeled_params need to be passed in the kwargs"

    def generate_model(self, data_handler: DataHandler):
        return self.model_type(**self.kwargs, data_handler=data_handler)

    def model_parameters(self):
        return tuple(self.kwargs[param] for param in self.model_parameters_names)


class FastAlphaModelTester:
    """
    ModelTester in which portfolio construction is simulated by always following the suggested Exposures from
    AlphaModels. All Tickers are traded with same weights (weights are constant across time).
    """

    def __init__(self, alpha_model_configs: Sequence[FastAlphaModelTesterConfig],
                 tickers: Sequence[Ticker],
                 contract_ticker_mapper: ContractTickerMapper, start_date: datetime, end_date: datetime,
                 data_handler: FastDataHandler, timer: SettableTimer, n_jobs: int = 1):

        self.logger = qf_logger.getChild(self.__class__.__name__)

        self._start_date = start_date
        self._end_date = end_date
        self._contract_ticker_mapper = contract_ticker_mapper

        self._alpha_model_configs = alpha_model_configs
        assert len(set(config.model_type for config in alpha_model_configs)) == 1, \
            "All passed FastAlphaModelTesterConfig should have the same alpha model type"

        self._model_type = alpha_model_configs[0].model_type

        self._data_handler = data_handler
        self._timer = timer

        self._tickers_to_contracts = self._get_valid_tickers_to_contracts(tickers)
        self._tickers = list(self._tickers_to_contracts.keys())
        self._n_jobs = n_jobs

        if type(self._data_handler) is not FastDataHandler:
            self.logger.warning("You are using a deprecated type of DataHandler. In FastAlphaModelsTester "
                                "use of FastDataHandler is suggested.")

    def test_alpha_models(self) -> BacktestSummary:
        print("{} parameters sets to be tested".format(len(self._alpha_model_configs)))
        prices_data_array = self._get_data_for_backtest()
        exposure_values_df_list = self._generate_exposures_for_all_params_sets()
        backtest_summary_elem_list = self._calculate_backtest_summary_elements(exposure_values_df_list,
                                                                               prices_data_array)
        backtest_summary = BacktestSummary(
            self._tickers, self._contract_ticker_mapper, self._model_type, backtest_summary_elem_list,
            self._start_date, self._end_date)
        return backtest_summary

    def _get_valid_tickers_to_contracts(self, tickers: Sequence[Ticker]) -> Dict[Ticker, Contract]:

        tickers_to_contracts = {}
        for ticker in tickers:
            try:
                if isinstance(ticker, FutureTicker):
                    ticker.initialize_data_provider(self._timer, self._data_handler)
                contract = self._contract_ticker_mapper.ticker_to_contract(ticker)
                tickers_to_contracts[ticker] = contract
            except NoValidTickerException:
                self.logger.warning("No valid ticker for {}".format(ticker.name))

        return tickers_to_contracts

    def _get_data_for_backtest(self) -> QFDataArray:
        """
        Creates a QFDataArray containing OHLCV values for all tickers passes to Fast Alpha Models Tester.
        """
        print("\nLoading all price values of tickers:")
        self._timer.set_current_time(self._end_date)
        tickers_dict = {}
        for ticker in tqdm(self._tickers, file=sys.stdout):
            if isinstance(ticker, FutureTicker):
                fc = FuturesChain(ticker, self._data_handler)
                tickers_dict[ticker] = fc.get_price(PriceField.ohlcv(), self._start_date, self._end_date,
                                                    Frequency.DAILY)
            else:
                tickers_dict[ticker] = self._data_handler.get_price(ticker, PriceField.ohlcv(), self._start_date,
                                                                    self._end_date)

        prices_data_array = tickers_dict_to_data_array(tickers_dict, self._tickers, PriceField.ohlcv())
        return prices_data_array

    def _generate_exposures_for_all_params_sets(self) -> List[QFDataFrame]:
        print("\nGenerating exposures:")
        exposure_values_df_list = Parallel(n_jobs=self._n_jobs)(delayed(self._generate_exposure_values)
                                                                (config, self._data_handler, self._tickers)
                                                                for config in
                                                                tqdm(self._alpha_model_configs, file=sys.stdout))
        print("\nFinished generation of exposures.")
        return exposure_values_df_list

    def _calculate_backtest_summary_elements(self, exposure_values_df_list: List[QFDataFrame],
                                             prices_data_array: QFDataArray) -> List[BacktestSummaryElement]:

        open_prices_df = self._get_open_prices(prices_data_array)
        open_to_open_returns_df = open_prices_df.to_simple_returns()

        print("\nGenerating backtest summaries:")
        tickers_for_backtests = [[ticker] for ticker in self._tickers]
        if len(self._tickers) > 1:
            tickers_for_backtests += [self._tickers]

        all_params = [(config, exposure_values_df, tickers)
                      for config, exposure_values_df in zip(self._alpha_model_configs, exposure_values_df_list)
                      for tickers in tickers_for_backtests]

        backtest_summary_elem_list = Parallel(n_jobs=self._n_jobs)(
            delayed(self._calculate_backtest_summary)(tickers, config, prices_data_array,
                                                      open_to_open_returns_df[tickers],
                                                      exposure_values_df[tickers])
            for config, exposure_values_df, tickers in tqdm(all_params, file=sys.stdout)
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
        tickers, _ = convert_to_list(tickers, Ticker)

        portfolio_rets_tms = self._calculate_portfolio_returns_tms(tickers, open_to_open_returns_df, exposure_values_df)
        trades = self._calculate_trades(prices_data_array, exposure_values_df)

        return BacktestSummaryElement(config.model_parameters(), config.model_parameters_names,
                                      portfolio_rets_tms, trades, tickers)

    def _calculate_portfolio_returns_tms(self, tickers, open_to_open_returns_df: QFDataFrame,
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

        open_to_open_returns_df = open_to_open_returns_df.dropna(how="all")
        shifted_signals_df = exposure_values_df.shift(2, axis=0)
        shifted_signals_df = shifted_signals_df.iloc[2:]

        daily_returns_of_strategies_df = shifted_signals_df * open_to_open_returns_df
        daily_returns_of_strategies_df = daily_returns_of_strategies_df.dropna(axis=0, how='all')

        daily_returns_of_strategies_df = cast_dataframe(
            daily_returns_of_strategies_df, SimpleReturnsDataFrame)  # type: SimpleReturnsDataFrame

        weights = Portfolio.one_over_n_weights(tickers)
        # for strategies based on more than one ticker (ex. VolLongShort) use the line below:
        # weights = QFSeries(np.ones(daily_returns_of_strategies_df.num_of_columns))

        portfolio_rets_tms, _ = Portfolio.constant_weights(daily_returns_of_strategies_df, weights)

        return portfolio_rets_tms

    def _calculate_trades(self, prices_array: QFDataArray, exposures_df: QFDataFrame) -> List[Trade]:
        trade_data_list = []
        shifted_signals_df = exposures_df.shift(1, axis=0)

        for ticker, exposures_tms in shifted_signals_df.iteritems():
            trade_data_partial_list = self.generate_trades_for_ticker(prices_array, exposures_tms, ticker)
            trade_data_list.extend(trade_data_partial_list)

        return trade_data_list

    def generate_trades_for_ticker(self, prices_array: QFDataArray, exposures_tms: pd.Series, ticker: Ticker) \
            -> List[Trade]:

        open_prices_tms = cast_data_array_to_proper_type(prices_array.loc[:, ticker, PriceField.Open],
                                                         use_prices_types=True)
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
                        contract=self._tickers_to_contracts[ticker],
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

    def _generate_exposure_values(self, config: FastAlphaModelTesterConfig, data_handler: FastDataHandler,
                                  tickers: Sequence[Ticker]):
        """
        For the given Alpha model and its parameters, generates the dataframe containing all exposure values, that
        will be returned by the model through signals.
        """

        model = config.generate_model(data_handler)

        current_exposures_values = QFSeries(index=pd.Index(tickers, name=TICKERS))
        current_exposures_values[:] = 0.0

        backtest_dates = pd.date_range(self._start_date, self._end_date, freq="B")

        exposure_values_df = QFDataFrame(
            index=backtest_dates,
            columns=pd.Index(tickers, name=TICKERS)
        )

        for ticker in tickers:
            if isinstance(ticker, FutureTicker):
                # Even if the tickers were already initialize, during pickling process, the data handler and timer
                # information is lost
                ticker.initialize_data_provider(self._timer, data_handler)

        for i, curr_datetime in enumerate(backtest_dates):
            new_exposures = QFSeries(index=tickers)
            self._timer.set_current_time(curr_datetime)

            for j, ticker, curr_exp_value in zip(count(), tickers, current_exposures_values):
                curr_exp = Exposure(curr_exp_value) if is_finite_number(curr_exp_value) else None
                try:
                    new_exp = model.calculate_exposure(ticker, curr_exp)
                except NoValidTickerException:
                    new_exp = None
                new_exposures.iloc[j] = new_exp.value if new_exp is not None else None

            # assuming that we always follow the new_exposures from strategy, disregarding confidence levels
            # and expected moves, looking only at the suggested exposure
            current_exposures_values = new_exposures
            exposure_values_df.iloc[i, :] = current_exposures_values.iloc[:]

        exposure_values_df = exposure_values_df.dropna(axis=1, how="all")
        return exposure_values_df
