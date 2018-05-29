from copy import deepcopy
from typing import Sequence

from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.backtesting.qstrader.risk_manager.base import AbstractRiskManager


class NaiveRiskManager(AbstractRiskManager):
    """
    This risk manager simply returns the incoming Order without modifying it.
    """

    def refine_orders(self, orders: Sequence[Order]) -> Sequence[Order]:
        # copying because someone calling this method expects to get a copy
        risk_adjusted_orders = [deepcopy(order) for order in orders]

        return risk_adjusted_orders
