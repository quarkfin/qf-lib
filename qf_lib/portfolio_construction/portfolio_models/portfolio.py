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

import abc
from typing import Tuple, Sequence

import numpy as np
import pandas as pd

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.dimension_names import TICKERS
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class Portfolio(metaclass=abc.ABCMeta):
    EPSILON = 1e-5

    @abc.abstractmethod
    def get_weights(self) -> QFSeries:
        """
        Returns
        -------
        a series indexed with names of assets containing weights (one for each asset).
        """
        pass

    @classmethod
    def logger(cls):
        return qf_logger.getChild(cls.__name__)

    @classmethod
    def constant_weights(cls, assets_rets_df: SimpleReturnsDataFrame, weights: QFSeries) \
            -> Tuple[SimpleReturnsSeries, QFDataFrame]:
        """
        Calculates the time series of portfolio returns (given the weights of portfolio's assets). Weights of assets
        are assumed to be the same all the time (there is a rebalancing on each time tick, e.g. every day if the series
        has a daily frequency).

        The method also calculates the allocation matrix. However since the weights are constant, so are
        the allocations.

        Parameters
        ----------
        assets_rets_df
            simple returns of assets which create the portfolio
        weights
            weights of assets creating the portfolio

        Returns
        -------
        Tuple[SimpleReturnsSeries, QFDataFrame]
            timeseries of portfolio's returns, dataframe indexed with dates and showing allocations in time (one column per asset)
        """
        assert len(weights) == assets_rets_df.num_of_columns

        weights_sum = weights.sum()
        if abs(weights_sum) - 1.0 > cls.EPSILON:
            cls.logger().warning("Sum of all weights is not equal to 1.0: sum(weights) = {:f}".format(weights_sum))

        num_of_assets = assets_rets_df.num_of_rows

        portfolio_rets = assets_rets_df.values.dot(weights)
        portfolio_rets_tms = SimpleReturnsSeries(data=portfolio_rets, index=assets_rets_df.index.copy())

        allocation_matrix = np.tile(weights, (num_of_assets, 1))
        allocation_df = QFDataFrame(data=allocation_matrix, index=assets_rets_df.index.copy(),
                                    columns=assets_rets_df.columns.copy())

        return portfolio_rets_tms, allocation_df

    @classmethod
    def drifting_weights(cls, assets_rets_df: SimpleReturnsDataFrame, weights: QFSeries) \
            -> Tuple[SimpleReturnsSeries, QFDataFrame]:
        """
        Calculates the time series of portfolio returns (given the initial weights of portfolio's assets).
        Weights of assets change over time because there is no rebalancing.

        The method also calculates the allocation matrix which shows what portfolio consists of on each date.

        Parameters
        ----------
        assets_rets_df
            simple returns of assets which create the portfolio
        weights
            weights of assets which create the portfolio

        Returns
        -------
        Tuple[SimpleReturnsSeries, QFDataFrame]
            timeseries of portfolio's returns, dataframe indexed with dates and showing allocations in time (one column per asset)
        """
        assert len(weights) == assets_rets_df.num_of_columns

        weights_sum = weights.sum()
        if abs(weights_sum - 1.0) > cls.EPSILON:
            cls.logger().warning("Sum of all weights is not equal to 1.0: sum(weights) = {:f}".format(weights_sum))

        # create a data frame with cumulative returns with a row of zeroes at the beginning
        assets_prices_df = assets_rets_df.to_prices(initial_prices=weights.values)
        portfolio_total_value_tms = cast_series(assets_prices_df.sum(axis=1), PricesSeries)
        portfolio_rets = portfolio_total_value_tms.to_simple_returns()
        portfolio_rets *= weights_sum  # scale returns so that they correspond to the level of investment

        # to get an allocation matrix one needs to divide each row of assets' prices by the cumulative
        # portfolio return at that time
        portfolio_total_values = portfolio_total_value_tms.values.reshape((-1, 1))  # make it a vertical vector
        normalizing_factor = np.tile(portfolio_total_values, (1, assets_prices_df.num_of_columns))
        allocation_matrix = assets_prices_df.values / normalizing_factor

        # to keep the correct level of investment values in allocation matrix need to be multiplied by the sum
        # of weights
        allocation_matrix *= weights_sum
        allocation_matrix = allocation_matrix[:-1, :]

        allocation_df = QFDataFrame(
            index=assets_rets_df.index.copy(), columns=assets_rets_df.columns.copy(), data=allocation_matrix)

        return portfolio_rets, allocation_df

    @classmethod
    def different_allocations_tms(cls, assets_rets_df: SimpleReturnsDataFrame, allocations_df: QFDataFrame) \
            -> SimpleReturnsSeries:
        """
        Calculates the time series of portfolio returns given the allocations on each date. The portfolio returns
        are calculated by multiplying returns of assets by corresponding allocations' values.

        Parameters
        ----------
        assets_rets_df
            simple returns of assets which create the portfolio
        allocations_df
            dataframe indexed with dates, showing allocations in time (one column per asset)

        Returns
        -------
        SimpleReturnsSeries
            timeseries of portfolio's returns
        """
        assert np.all(assets_rets_df.columns.values == allocations_df.columns.values), \
            "Different column values for assets and allocation matrix"
        assert np.all(assets_rets_df.index.values == allocations_df.index.values), \
            "Different dates for assets and allocation matrix"

        # get indices of rows for which: sum of weights is greater than 1. The result of where is a tuple (for a vector
        # it's a 1-element tuple, for a matrix -- a 2-element tuple and so on). Thus it's necessary to unwrap the result
        # from a tuple, to get the array of indices (instead of 1-elem. tuple consisted of an array).
        incorrect_weights_rows = np.abs(allocations_df.sum(axis=1) - 1.0) > cls.EPSILON  # type: np.ndarray

        if np.any(incorrect_weights_rows):
            dates = allocations_df.index.values[incorrect_weights_rows]
            dates_str = ", ".join([date_to_str(date) for date in dates])

            cls.logger().warning("Weights don't sum up to 1 for the following dates: " + dates_str)

        scaled_returns = assets_rets_df * allocations_df  # type: np.ndarray
        portfolio_rets = scaled_returns.sum(axis=1)
        portfolio_rets_tms = SimpleReturnsSeries(data=portfolio_rets, index=allocations_df.index.copy())

        return portfolio_rets_tms

    @classmethod
    def one_over_n_weights(cls, tickers: Sequence[Ticker]) -> QFSeries:
        """
        Calculates the one-over-n weights for given tickers.
        """
        num_of_tickers = len(tickers)
        weight_of_each_asset = 1 / num_of_tickers

        weights_values = [weight_of_each_asset] * num_of_tickers
        weights = QFSeries(index=pd.Index(tickers, name=TICKERS), data=weights_values)

        return weights
