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
from datetime import datetime
from typing import Sequence, Optional

import numpy as np

from qf_lib.backtesting.execution_handler.slippage.base import Slippage
from qf_lib.backtesting.order.order import Order
from qf_lib.data_providers.data_provider import DataProvider


class FixedSlippage(Slippage):
    """
    Slippage which always adds (or subtracts if short sale) certain absolute amount of money to the price.
    """

    def __init__(self, slippage_per_share: float, data_provider: DataProvider,
                 max_volume_share_limit: Optional[float] = None):
        super().__init__(data_provider, max_volume_share_limit)
        self.slippage_per_share = slippage_per_share

    def _get_fill_prices(self, date: datetime, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float],
                         fill_volumes: Sequence[int]) -> Sequence[float]:
        fill_volumes = np.array([order.quantity for order in orders])
        fill_prices = np.array(no_slippage_fill_prices) + np.copysign(self.slippage_per_share, fill_volumes)

        return fill_prices
