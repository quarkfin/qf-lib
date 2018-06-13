from abc import ABCMeta, abstractmethod
from typing import Sequence

from qf_lib.backtesting.order.order import Order


class PositionSizer(object, metaclass=ABCMeta):
    """
    The PositionSizer abstract class modifies
    the quantity (or not) of any share transacted
    """

    @abstractmethod
    def size_orders(self, initial_orders: Sequence[Order]) -> Sequence[Order]:
        """
        Creates a list of modified Orders where proper sizing has been applied. The original Orders are not modified.
        """
        raise NotImplementedError("Should implement size_order()")
