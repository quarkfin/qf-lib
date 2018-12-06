from copy import deepcopy
from typing import Sequence

from qf_lib.backtesting.order.order import Order
from .position_sizer import PositionSizer


class PercentAtRiskPositionSizer(PositionSizer):
    """
    This PercentAtRiskPositionSizer is using a predefined "percentage at risk" value to size the positions.

    """

    def size_orders(self, initial_orders: Sequence[Order]) -> Sequence[Order]:
        # copying because the caller of this method expects to get a copy of an order
        return [deepcopy(initial_order) for initial_order in initial_orders]
