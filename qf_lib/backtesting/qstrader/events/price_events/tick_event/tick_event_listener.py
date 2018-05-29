import abc

from qf_lib.backtesting.qstrader.events.event_base import EventListener
from qf_lib.backtesting.qstrader.events.price_events.tick_event.tick_event import TickEvent


class TickEventListener(EventListener[TickEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_tick_event(self, event: TickEvent):
        pass
