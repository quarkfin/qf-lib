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

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.portfolio_construction.optimizers.helpers.common_constraint_helpers import prepare_upper_bounds_vector, \
    put_weights_below_constraint
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class RiskParityPortfolio(Portfolio):
    """
    Class used for constructing a portfolio in which weight of each asset is proportional to the inverse volatility
    that it has. For each asset the standard deviation of its returns is calculated and the inverse of that result
    is the weight of the asset.
    """

    def __init__(self, input_dataframe: QFDataFrame, upper_constraint: Union[float, Sequence[float]] = None):
        self.assets_returns_df = input_dataframe.to_simple_returns()
        assets_number = self.assets_returns_df.shape[1]
        self.upper_constraints = prepare_upper_bounds_vector(assets_number, upper_constraint)

    def get_weights(self) -> QFSeries:
        num_of_assets = len(self.assets_returns_df.columns)
        volatilities = np.array([np.std(asset_tms) for _, asset_tms in self.assets_returns_df.iteritems()])

        weights = np.ones(num_of_assets) / volatilities
        weights /= weights.sum()

        if self.upper_constraints is not None:
            weights = put_weights_below_constraint(weights, self.upper_constraints)

        weights_series = QFSeries(data=weights, index=self.assets_returns_df.columns.copy())

        return weights_series
