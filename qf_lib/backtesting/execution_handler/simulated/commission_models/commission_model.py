from abc import ABCMeta, abstractmethod

from qf_lib.backtesting.order.order import Order


class CommissionModel(object, metaclass=ABCMeta):
    @abstractmethod
    def calculate_commission(self, order: Order, fill_price: float):
        pass
