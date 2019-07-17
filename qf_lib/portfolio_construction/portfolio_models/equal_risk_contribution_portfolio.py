from typing import Union, Sequence

import pandas as pd

from qf_lib.common.timeseries_analysis.risk_contribution_analysis import RiskContributionAnalysis
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.portfolio_construction.optimizers.nonlinear_function_optimizer import NonlinearFunctionOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class EqualRiskContributionPortfolio(Portfolio):
    """ Class used for constructing an ERC portfolio. """

    def __init__(self, cov_matrix: QFDataFrame, upper_constraint: Union[float, Sequence[float]] = None):
        self.cov_matrix = cov_matrix
        self.upper_constraint = upper_constraint
        self.max_iter = 10000  # maximal number of iterations during finding the solution

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_weights(self) -> pd.Series:
        def minimised_func(weights_values: Sequence[float]):
            weights_series = pd.Series(data=weights_values, index=self.cov_matrix.columns)
            return RiskContributionAnalysis.get_distance_to_equal_risk_contrib(self.cov_matrix, weights_series)

        weights = NonlinearFunctionOptimizer.get_weights(
            minimised_func, max_iter=self.max_iter, upper_constraints=self.upper_constraint,
            num_of_assets=self.cov_matrix.shape[1])
        weights = pd.Series(data=weights, index=self.cov_matrix.columns.copy())

        if not RiskContributionAnalysis.is_equal_risk_contribution(self.cov_matrix, weights):
            self.logger.warning("EqualRiskContributionPortfolio: calculated weights do not create an ERC Portfolio.")

        return weights
