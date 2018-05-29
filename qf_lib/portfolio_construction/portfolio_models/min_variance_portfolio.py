from typing import Union, Sequence

import pandas as pd

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
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

    def get_weights(self) -> pd.Series:
        P = self.cov_matrix.values
        weights = QuadraticOptimizer.get_optimal_weights(P, upper_constraints=self.upper_constraint)

        return pd.Series(data=weights, index=self.cov_matrix.columns)
