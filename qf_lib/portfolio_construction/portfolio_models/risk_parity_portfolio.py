from typing import Union, Sequence

import numpy as np
import pandas as pd

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
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

    def get_weights(self) -> pd.Series:
        num_of_assets = len(self.assets_returns_df.columns)
        volatilities = np.array([np.std(asset_tms) for _, asset_tms in self.assets_returns_df.iteritems()])

        weights = np.ones(num_of_assets) / volatilities
        weights /= weights.sum()

        if self.upper_constraints is not None:
            weights = put_weights_below_constraint(weights, self.upper_constraints)

        weights_series = pd.Series(data=weights, index=self.assets_returns_df.columns.copy())

        return weights_series
