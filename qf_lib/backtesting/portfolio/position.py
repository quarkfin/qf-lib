from abc import ABCMeta, abstractmethod

from qf_lib.backtesting.contract.contract import Contract


class Position(metaclass=ABCMeta):
    @abstractmethod
    def contract(self) -> Contract:
        pass

    @abstractmethod
    def quantity(self) -> int:
        pass

    @abstractmethod
    def avg_cost_per_share(self) -> float:
        pass
