import abc

from qf_lib.backtesting.qstrader.events.event_base import EventListener
from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent


class FillEventListener(EventListener[FillEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_fill_event(self, event: FillEvent):
        pass
