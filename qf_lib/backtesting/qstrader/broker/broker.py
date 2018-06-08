from abc import ABCMeta, abstractmethod
from typing import List, Optional

from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.backtesting.qstrader.portfolio.position import Position


class Broker(object, metaclass=ABCMeta):
    @abstractmethod
    def get_portfolio_value(self) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        pass

    @abstractmethod
    def place_order(self, order: Order) -> int:
        pass

    @abstractmethod
    def get_open_orders(self)-> Optional[List[Order]]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: int):
        """
        Raises
        ------
        OrderCancellingException if Order wasn't cancelled
        """
        pass

    @abstractmethod
    def cancel_all_open_orders(self):
        pass
