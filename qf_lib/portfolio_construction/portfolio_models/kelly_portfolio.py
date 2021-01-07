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

from typing import Union, Sequence

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.quadratic_optimizer import QuadraticOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class KellyPortfolio(Portfolio):
    """ Class used for constructing a portfolio based on Kelly's criterion. """

    def __init__(self, cov_matrix: QFDataFrame, mean_returns: QFSeries,
                 upper_constraint: Union[float, Sequence[float]] = None):
        self.upper_constraint = upper_constraint
        self.cov_matrix = cov_matrix
        self.mean_returns = mean_returns

    def get_weights(self) -> QFSeries:
        P = self.cov_matrix.values
        q = - self.mean_returns.values
        weights = QuadraticOptimizer.get_optimal_weights(P, q, self.upper_constraint)

        return QFSeries(data=weights, index=self.cov_matrix.columns)
