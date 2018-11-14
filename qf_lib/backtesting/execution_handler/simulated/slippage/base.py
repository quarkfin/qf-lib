from abc import ABCMeta, abstractmethod
from typing import Sequence

from qf_lib.backtesting.order.order import Order


class Slippage(object, metaclass=ABCMeta):

    @abstractmethod
    def calc_fill_prices(self, orders: Sequence[Order]) -> Sequence[float]:
        """
        Calculates fill prices for Orders. For Orders that can't be executed (missing security price, etc.) float('nan")
        will be returned.

        Parameters
        ----------
        orders
            sequence of Orders for which the fill price should be calculated

        Returns
        -------
        sequence of fill prices (order corresponds to the order of orders provided as an argument of the method)
        """
        pass
