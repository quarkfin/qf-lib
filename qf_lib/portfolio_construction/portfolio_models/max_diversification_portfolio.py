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

import numpy as np
from cvxopt import matrix
from cvxopt.coneprog import qp
import warnings

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.helpers.quadratic_constraints_helpers import \
    each_weight_greater_than_0_constraint, merge_constraints, upper_bound_constraint
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class MaxDiversificationPortfolio(Portfolio):
    """
    Class used for constructing a Max Diversification portfolio.
    See: http://allaboutalpha.com/blog/2011/03/27/the-most-diversified-portfolio/
    """

    optimizer_options = {
        'show_progress': False
    }

    def __init__(self, cov_matrix: QFDataFrame, std_of_assets: QFSeries,
                 upper_constraint: Union[float, Sequence[float]] = None):
        self.cov_matrix = cov_matrix
        self.std_of_assets = std_of_assets
        self.upper_constraint = upper_constraint
        self.upper_bound_tolerance = 0.012
        self.max_iter = 10  # maximal number of iterations during finding the solution

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_weights(self) -> QFSeries:
        assets_number = self.cov_matrix.shape[1]
        st_devs = self.std_of_assets.values
        st_devs = st_devs.reshape((1, -1))  # make it a horizontal vector

        P = matrix(self.cov_matrix.values)
        q = matrix(0.0, (assets_number, 1))

        A = matrix(st_devs)
        b = matrix([1.0])

        G_lower_bound, h_lower_bound = each_weight_greater_than_0_constraint(assets_number)

        if self.upper_constraint is not None:
            G_upper_bound, h_upper_bound = self._get_upper_bound_constraints(P, q, G_lower_bound, h_lower_bound, A, b)
            G, h = merge_constraints(G_lower_bound, h_lower_bound, G_upper_bound, h_upper_bound)
        else:
            G, h = G_lower_bound, h_lower_bound

        result = qp(P, q, G, h, A, b, options=self.optimizer_options)
        dummy_weights = np.array(result['x']).squeeze()
        scaled_weights = dummy_weights / dummy_weights.sum()
        weights_series = QFSeries(data=scaled_weights, index=self.cov_matrix.columns.values)

        return weights_series

    def calculate_diversification_ratio(self, weights: QFSeries) -> float:
        """
        Calculates a Diversification Ratio for the portfolio taking the returns of assets (set for the portfolio)
        and the weights provided in the parameter. For two or more assets diversification ratio will be greater or equal
        to one. The higher it is, the better.

        Parameters
        ----------
        weights: pandas.Series
            series of weights indexed with names of assets

        Returns
        -------
        float
            Diversification Ratio
        """
        epsilon = 1e-06
        weights_sum = weights.sum()
        if abs(weights_sum - 1) > epsilon:
            self.logger.warning(
                "Warning: sum of all weights is not equal to 1. sum(weights) = {:f}".format(weights_sum))
            self.logger.info('Adjusting weights...')
            weights = weights / weights_sum

        weights_values = weights.values
        weights_values = weights_values.reshape((-1, 1))  # make it a vertical vector
        std_of_elements = self.std_of_assets.values
        std_of_elements = std_of_elements.reshape((1, -1))  # make it a horizontal vector

        avg_volatility = std_of_elements.dot(weights_values)
        # portfolio volatility = sqrt(w'*E*w)
        portfolio_volatility = np.sqrt((weights_values.T.dot(self.cov_matrix.values)).dot(weights_values))

        diversification_ratio = avg_volatility / portfolio_volatility
        return float(diversification_ratio)

    # noinspection PyUnresolvedReferences
    def _get_upper_bound_constraints(self, P, q, G_lower_bound, h_lower_bound, A, b):
        upper_bound = self.upper_constraint

        assets_number = self.cov_matrix.shape[1]
        if isinstance(upper_bound, float):
            upper_bound = [upper_bound] * assets_number

        h_upper_bound_scaled = None
        G_upper_bound, h_upper_bound = upper_bound_constraint(assets_number, upper_bound)

        prev_scaling_factor = 1
        scaling_factor = 30  # experimentally chosen
        loop_iter = 1

        while abs(prev_scaling_factor - scaling_factor) > self.upper_bound_tolerance:
            h_upper_bound_scaled = h_upper_bound * scaling_factor
            G, h = merge_constraints(G_lower_bound, h_lower_bound, G_upper_bound, h_upper_bound_scaled)

            result = qp(P, q, G, h, A, b, options=self.optimizer_options)
            dummy_weights = np.array(result['x']).squeeze()

            prev_scaling_factor = scaling_factor
            scaling_factor = dummy_weights.sum()

            loop_iter += 1
            if loop_iter >= self.max_iter:
                warnings.warn("Max. number of iterations achieved during searching for a weights scaling factor.")
                break

        return G_upper_bound, h_upper_bound_scaled
