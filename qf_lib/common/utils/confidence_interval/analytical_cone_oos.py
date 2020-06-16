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

from math import exp

import numpy as np
from pandas import Int64Index

from qf_lib.common.utils.confidence_interval.analytical_cone_base import AnalyticalConeBase
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class AnalyticalConeOOS(AnalyticalConeBase):
    def calculate_aggregated_cone_oos_only(
            self, oos_series: QFSeries, is_mean_return: float, is_sigma: float, number_of_std: float) -> QFDataFrame:
        """
        This functions does not need the IS history, only the IS statistics.

        Parameters
        ----------
        oos_series
            series that is plotted on the cone - corresponds to the oos returns
        is_mean_return
            mean daily log return of the strategy In Sample
        is_sigma
            std of daily log returns of the strategy In Sample
        number_of_std
            corresponds to the randomness of the stochastic process. reflects number of standard deviations
            to get expected values for. For example 1.0 means 1 standard deviation above the expected value.

        Returns
        -------
        QFDataFrame: contains values corresponding to Strategy, Mean and Std. Values are indexed by number of days
            from which given cone was evaluated
        """

        log_returns_tms = oos_series.to_log_returns()
        nr_of_data_points = oos_series.size

        strategy_values = np.empty(nr_of_data_points)
        expected_values = np.empty(nr_of_data_points)

        for i in range(nr_of_data_points):
            cone_start_idx = i + 1

            # calculate total return of the strategy
            oos_log_returns = log_returns_tms[cone_start_idx:]
            total_strategy_return = exp(oos_log_returns.sum())  # 1 + percentage return

            # calculate expectation
            number_of_steps = len(oos_log_returns)
            starting_price = 1  # we take 1 as a base value
            total_expected_return = self.get_expected_value(
                is_mean_return, is_sigma, starting_price, number_of_steps, number_of_std)

            # writing to the array starting from the last array element and then moving towards the first one
            strategy_values[-i - 1] = total_strategy_return
            expected_values[-i - 1] = total_expected_return

        index = Int64Index(range(0, nr_of_data_points))

        strategy_values_tms = PricesSeries(index=index, data=strategy_values)
        expected_tms = QFSeries(index=index, data=expected_values)

        return QFDataFrame({
            'Strategy': strategy_values_tms,
            'Expectation': expected_tms,
        })
