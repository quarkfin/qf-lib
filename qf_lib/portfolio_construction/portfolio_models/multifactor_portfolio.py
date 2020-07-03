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

import pandas as pd
from scipy.stats import zscore

from qf_lib.portfolio_construction.optimizers.quadratic_optimizer import QuadraticOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class PortfolioParameters(object):
    def __init__(self, scale, variance_weight, mean_weight, max_dd_weight, skewness_weight):
        self.scale = scale
        self.variance_weight = variance_weight
        self.mean_weight = mean_weight
        self.max_dd_weight = max_dd_weight
        self.skewness_weight = skewness_weight


class MultiFactorPortfolio(Portfolio):
    """
    Class used for constructing a portfolio. It optimizes a portfolio considering:

    - variance of a portfolio(minimizing),
    - mean return of portfolio's assets (maximizing),
    - max drawdown of the portfolio (minimizing).
    """

    def __init__(self, covariance_matrix: pd.DataFrame,
                 variance: pd.Series, mean: pd.Series, max_drawdown: pd.Series, skewness: pd.Series,
                 parameters: PortfolioParameters, upper_constraint: Union[float, Sequence[float]] = None):
        self.covariance_matrix = covariance_matrix
        self.variance = variance
        self.mean = mean
        self.max_dd = max_drawdown  # dd is expressed in positive numbers, for example 0.32 means max dd of 32%
        self.skewness = skewness
        self.parameters = parameters
        self.upper_constraint = upper_constraint

    def get_weights(self) -> pd.Series:
        P = self.covariance_matrix

        # normalize factors by assuring mean=0 and std=1 and multiply them by proper weights
        variance_part = -self.parameters.variance_weight * zscore(self.variance)  # minus sign because it's maximised
        mean_part = -self.parameters.mean_weight * zscore(self.mean)  # minus sign because it's maximised
        max_dd_part = self.parameters.max_dd_weight * zscore(self.max_dd)  # this is minimised, so no minus sign
        # this is maximized (we want right tale to be larger), minus sign
        skewness_part = -self.parameters.skewness_weight * zscore(self.skewness)

        # calculate and scale score of each assets
        q = self.parameters.scale * (variance_part + mean_part + max_dd_part + skewness_part)
        weights = QuadraticOptimizer.get_optimal_weights(P.values, q, upper_constraints=self.upper_constraint)

        return pd.Series(data=weights, index=self.covariance_matrix.columns)
