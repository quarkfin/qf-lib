import abc

from qf_lib.backtesting.qstrader.events.event_base import EventListener
from qf_lib.backtesting.qstrader.events.price_events.bar_event.bar_event import BarEvent


class BarEventListener(EventListener[BarEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_bar_event(self, event: BarEvent):
        pass
