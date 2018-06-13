from abc import ABCMeta, abstractmethod


class CommissionModel(object, metaclass=ABCMeta):
    @abstractmethod
    def calculate_commission(self, quantity, fill_price):
        pass
