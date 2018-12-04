from typing import Sequence, Tuple

import numpy as np

from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.order.order import Order


class FixedSlippage(Slippage):
    def __init__(self, slippage_per_share: float):
        self.slippage_per_share = slippage_per_share

    def apply_slippage(self, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float]) \
            -> Tuple[Sequence[float], Sequence[int]]:
        fill_volumes = np.array([order.quantity for order in orders])
        fill_prices = np.array(no_slippage_fill_prices) + np.copysign(self.slippage_per_share, fill_volumes)

        return fill_prices, fill_volumes
