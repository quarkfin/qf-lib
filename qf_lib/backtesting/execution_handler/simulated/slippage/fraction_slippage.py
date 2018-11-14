import math
from typing import Sequence

from qf_lib.backtesting.execution_handler.simulated.slippage.base import Slippage
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order


class FractionSlippage(Slippage):
    """
    Calculates the slippage by using some fixed fraction of the current securities' price (e.g. always 0.01%).
    """

    def __init__(self, slippage_rate: float):
        self.slippage_rate = slippage_rate

    def apply_slippage(self, orders: Sequence[Order], no_slippage_fill_prices: Sequence[float]) -> Sequence[float]:
        fill_prices = []

        for order, no_slippage_price in zip(orders, no_slippage_fill_prices):
            if isinstance(order.execution_style, MarketOrder):
                fill_price = self._get_single_fill_price(order, no_slippage_price)
            else:
                # TODO support StopOrders
                fill_price = float("nan")

            fill_prices.append(fill_price)

        return fill_prices

    def _get_single_fill_price(self, order, no_slippage_price):
        if math.isnan(no_slippage_price):
            fill_price = float('nan')
        else:
            if order.quantity > 0:  # BUY Order
                multiplier = 1 + self.slippage_rate
            else:  # SELL Order
                multiplier = 1 - self.slippage_rate

            fill_price = no_slippage_price * multiplier

        return fill_price
