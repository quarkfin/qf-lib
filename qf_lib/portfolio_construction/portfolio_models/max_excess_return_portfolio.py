from typing import Union, Sequence

import pandas as pd
from numpy import ndarray

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.quadratic_optimizer import QuadraticOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class MaxExcessReturnPortfolio(Portfolio):
    """
    Class used for constructing a portfolio which is optimized considering its excess return (maximized). Excess
    return is defined as: portfolio volatility - 0.5 * weighted variance of individual assets.
    """

    def __init__(self, cov_matrix: QFDataFrame, variance_of_assets: QFSeries,
                 upper_constraint: Union[float, Sequence[float]] = None):
        self.cov_matrix = cov_matrix
        self.variance_of_assets = variance_of_assets
        self.upper_constraint = upper_constraint

    def get_weights(self) -> pd.Series:
        P = self.cov_matrix.values
        q = -0.5 * self.variance_of_assets.values  # type: ndarray
        weights = QuadraticOptimizer.get_optimal_weights(P, q, upper_constraints=self.upper_constraint)

        return pd.Series(data=weights, index=self.cov_matrix.columns)
