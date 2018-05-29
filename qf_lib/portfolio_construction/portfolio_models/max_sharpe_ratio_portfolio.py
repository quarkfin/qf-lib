import logging
from typing import Union, Sequence

import numpy as np
import pandas as pd
import scipy

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.quadratic_optimizer import QuadraticOptimizer
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class MaxSharpeRatioPortfolio(Portfolio):
    """
    Class used for constructing a Max Sharpe Ratio portfolio.
    see: http://people.stat.sc.edu/sshen/events/backtesting/reference/maximizing%20the%20sharpe%20ratio.pdf
    """

    def __init__(self, cov_matrix: QFDataFrame, mean_returns: QFSeries,
                 upper_constraint: Union[float, Sequence[float]] = None,
                 risk_free_rate: float = 0.0, max_iter: int = 10000):
        self.cov_matrix = cov_matrix
        self.mean_returns = mean_returns
        self.upper_constraint = upper_constraint
        self.risk_free_rate = risk_free_rate
        self.max_iter = max_iter

    def get_weights(self) -> pd.Series:
        cov_matrix = self.cov_matrix.values
        mean_returns = self.mean_returns.values

        def minimised_func(k: np.ndarray) -> float:
            k = k.squeeze()
            scaled_mean_returns = -k * mean_returns  # type: np.ndarray
            weights = QuadraticOptimizer.get_optimal_weights(cov_matrix, scaled_mean_returns, self.upper_constraint)
            weights = weights.reshape((-1, 1))  # make it vertical
            portfolio_excess_ret = (mean_returns - self.risk_free_rate).dot(weights)
            portfolio_vol = np.sqrt((weights.T.dot(cov_matrix)).dot(weights))  # sqrt(w'*E*w)

            portfolio_excess_ret = portfolio_excess_ret.squeeze()
            portfolio_vol = portfolio_vol.squeeze()

            sr = portfolio_excess_ret / portfolio_vol
            return -sr

        k = self._find_scaling_factor_for_returns(minimised_func)
        scaled_mean_returns = -k * mean_returns
        weights = QuadraticOptimizer.get_optimal_weights(cov_matrix, scaled_mean_returns, self.upper_constraint)
        weights_series = pd.Series(data=weights, index=self.cov_matrix.columns)

        return weights_series

    def _find_scaling_factor_for_returns(self, minimised_func):
        options = {
            'maxiter': self.max_iter,
            'disp': False
        }
        optimization_result = scipy.optimize.minimize(fun=minimised_func, x0=np.array([0]), method='L-BFGS-B',
                                                      bounds=[(0, None)], options=options)

        if not optimization_result.success:
            logging.warning("Unsuccessful optimization: " + optimization_result.message)

        k = optimization_result.x
        k = k.squeeze()
        return k
