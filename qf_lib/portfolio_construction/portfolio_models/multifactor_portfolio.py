from typing import Union, Sequence

import pandas as pd
from scipy.stats import zscore

from qf_lib.portfolio_construction.optimizers.quadratic_optimizer import QuadraticOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class PortfolioParameters(object):
    def __init__(self, scale, variance_weight, mean_weight, max_dd_weight):
        self.scale = scale
        self.variance_weight = variance_weight
        self.mean_weight = mean_weight
        self.max_dd_weight = max_dd_weight


class MultiFactorPortfolio(Portfolio):
    """
    Class used for constructing a portfolio which optimizes a portfolio considering:
    - variance of a portfolio(minimizing),
    - mean return of portfolio's assets (maximizing),
    - max drawdown of the portfolio (minimizing).
    """

    def __init__(self, covariance_matrix: pd.DataFrame, variance: pd.Series, mean: pd.Series, max_drawdown: pd.Series,
                 parameters: PortfolioParameters, upper_constraint: Union[float, Sequence[float]] = None):
        self.covariance_matrix = covariance_matrix
        self.variance = variance
        self.mean = mean
        self.max_dd = max_drawdown
        self.parameters = parameters
        self.upper_constraint = upper_constraint

    def get_weights(self) -> pd.Series:
        P = self.covariance_matrix

        # normalize factors by assuring mean=0 and std=1 and multiply them by proper weights
        variance_part = -self.parameters.variance_weight * zscore(self.variance)  # minus sign because it's maximised
        mean_part = -self.parameters.mean_weight * zscore(self.mean)  # minus sign because it's maximised
        max_dd_part = self.parameters.max_dd_weight * zscore(self.max_dd)  # this is minimised, so no minus sign

        # calculate and scale score of each assets
        q = self.parameters.scale * (variance_part + mean_part + max_dd_part)
        weights = QuadraticOptimizer.get_optimal_weights(P.values, q, upper_constraints=self.upper_constraint)

        return pd.Series(data=weights, index=self.covariance_matrix.columns)
