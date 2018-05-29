import abc
from typing import Sequence

from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.common.utils.dateutils.timer import Timer


class AbstractRiskManager(object, metaclass=abc.ABCMeta):
    """
    The AbstractRiskManager abstract class lets the sized Order through, creates the risk-adjusted Order object
    and adds it to a list. It is possible for the risk manager to generate more than one Order from the sized Order
    (e.g. it can introduce some hedging so another asset will be bought as well).
    """

    def __init__(self, timer: Timer) -> None:
        self.timer = timer

    @abc.abstractmethod
    def refine_orders(self, orders: Sequence[Order]) -> Sequence[Order]:
        """
        Modifies the original Order by changing its size or completely rejects it. The modified Order is returned
        (the original one is not modified). If the Order is rejected completely, then None is returned.
        """
        raise NotImplementedError("Should implement refine_orders()")
