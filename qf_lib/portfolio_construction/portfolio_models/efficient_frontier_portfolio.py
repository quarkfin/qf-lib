from typing import Union, Sequence

import pandas as pd

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.quadratic_optimizer import QuadraticOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class EfficientFrontierPortfolio(Portfolio):
    """
    Class used for constructing a portfolio, for which the weight of assets' mean returns can be adjusted against
    the weight of the covariance of assets.
    """

    def __init__(self, cov_matrix: QFDataFrame, mean_returns: QFSeries, k: int,
                 upper_constraint: Union[float, Sequence[float]] = None):
        self.upper_constraint = upper_constraint
        self.cov_matrix = cov_matrix
        self.k = k
        self.mean_returns = mean_returns

    def get_weights(self) -> pd.Series:
        P = self.cov_matrix.values
        q = - self.mean_returns.values * self.k
        weights = QuadraticOptimizer.get_optimal_weights(P, q, self.upper_constraint)

        return pd.Series(data=weights, index=self.cov_matrix.columns)
