from abc import ABCMeta, abstractmethod

from qf_lib.backtesting.qstrader.contract.contract import Contract


class Position(metaclass=ABCMeta):
    @abstractmethod
    def contract(self) ->Contract:
        pass

    @abstractmethod
    def quantity(self) -> float:
        pass

    @abstractmethod
    def avg_cost_per_share(self) -> float:
        pass
