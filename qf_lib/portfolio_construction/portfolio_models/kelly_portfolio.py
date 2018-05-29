from typing import Union, Sequence

import pandas as pd

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

    def get_weights(self) -> pd.Series:
        P = self.cov_matrix.values
        q = - self.mean_returns.values
        weights = QuadraticOptimizer.get_optimal_weights(P, q, self.upper_constraint)

        return pd.Series(data=weights, index=self.cov_matrix.columns)
