from typing import Union, Sequence

import pandas as pd
from scipy.stats import zscore

from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
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

    def __init__(self, input_dataframe: QFDataFrame, covariance_matrix: pd.DataFrame, parameters: PortfolioParameters,
                 upper_constraint: Union[float, Sequence[float]] = None):
        self.assets_returns_df = input_dataframe.to_simple_returns()
        self.covariance_matrix = covariance_matrix
        self.parameters = parameters
        self.upper_constraint = upper_constraint

    def get_weights(self) -> pd.Series:
        P = self.covariance_matrix

        variance = self.assets_returns_df.var()
        mean = self.assets_returns_df.mean()
        max_dd = max_drawdown(self.assets_returns_df)

        # normalize factors by assuring mean=0 and std=1 and multiply them by proper weights
        variance_part = -self.parameters.variance_weight * zscore(variance)  # minus sign because it's maximised
        mean_part = -self.parameters.mean_weight * zscore(mean)  # minus sign because it's maximised
        max_dd_part = self.parameters.max_dd_weight * zscore(max_dd)  # this is minimised, so no minus sign in front

        # calculate and scale score of each assets
        q = self.parameters.scale * (variance_part + mean_part + max_dd_part)
        weights = QuadraticOptimizer.get_optimal_weights(P.values, q, upper_constraints=self.upper_constraint)

        return pd.Series(data=weights, index=self.assets_returns_df.columns)
