from copy import deepcopy
from typing import Sequence

from qf_lib.backtesting.qstrader.order.order import Order
from .base import AbstractPositionSizer


class NaivePositionSizer(AbstractPositionSizer):
    """
    This NaivePositionSizer object follows all suggestions from the initial order without modification.
    Useful for testing simpler strategies that do not reside in a larger risk-managed portfolio.
    """

    def size_orders(self, initial_orders: Sequence[Order]) -> Sequence[Order]:
        # copying because the caller of this method expects to get a copy of an order
        return [deepcopy(initial_order) for initial_order in initial_orders]
