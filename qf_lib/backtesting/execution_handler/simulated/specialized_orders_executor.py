from abc import abstractmethod
from typing import Sequence, List, Optional

from qf_lib.backtesting.order.order import Order


class SpecializedOrdersExecutor(object):
    def __init__(self, order_id_generator):
        self._order_id_generator = order_id_generator

    @abstractmethod
    def accept_orders(self, orders: Sequence[Order]) -> List[int]:
        pass

    @abstractmethod
    def execute_orders(self) -> None:
        pass

    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: int) -> Optional[Order]:
        """
        Cancel Order of given id (if it exists). Returns the cancelled Order or None if couldn't find the Order
        of given id.
        """
        pass

    @abstractmethod
    def cancel_all_open_orders(self):
        pass

    def _get_next_order_id(self) -> int:
        return next(self._order_id_generator)
