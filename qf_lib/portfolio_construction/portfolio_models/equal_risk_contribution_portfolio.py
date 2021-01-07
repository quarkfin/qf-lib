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

from qf_lib.common.timeseries_analysis.risk_contribution_analysis import RiskContributionAnalysis
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.nonlinear_function_optimizer import NonlinearFunctionOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class EqualRiskContributionPortfolio(Portfolio):
    """ Class used for constructing an ERC portfolio. """

    def __init__(self, cov_matrix: QFDataFrame, upper_constraint: Union[float, Sequence[float]] = None):
        self.cov_matrix = cov_matrix
        self.upper_constraint = upper_constraint
        self.max_iter = 10000  # maximal number of iterations during finding the solution

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_weights(self) -> QFSeries:
        def minimised_func(weights_values: Sequence[float]):
            weights_series = QFSeries(data=weights_values, index=self.cov_matrix.columns)
            return RiskContributionAnalysis.get_distance_to_equal_risk_contrib(self.cov_matrix, weights_series)

        weights = NonlinearFunctionOptimizer.get_weights(
            minimised_func, max_iter=self.max_iter, upper_constraints=self.upper_constraint,
            num_of_assets=self.cov_matrix.shape[1])
        weights = QFSeries(data=weights, index=self.cov_matrix.columns.copy())

        if not RiskContributionAnalysis.is_equal_risk_contribution(self.cov_matrix, weights):
            self.logger.warning("EqualRiskContributionPortfolio: calculated weights do not create an ERC Portfolio.")

        return weights
