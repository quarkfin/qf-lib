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


class MinVariancePortfolio(Portfolio):
    """
    Class used for constructing a min-variance portfolio (the one which is optimized considering it variance,
    which is minimized).
    """

    def __init__(self, cov_matrix: QFDataFrame, upper_constraint: Union[float, Sequence[float]] = None):
        self.cov_matrix = cov_matrix
        self.upper_constraint = upper_constraint

    def get_weights(self) -> QFSeries:
        P = self.cov_matrix.values
        weights = QuadraticOptimizer.get_optimal_weights(P, upper_constraints=self.upper_constraint)

        return QFSeries(data=weights, index=self.cov_matrix.columns)
