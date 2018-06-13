import abc

from qf_lib.backtesting.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.events.event_base import EventListener


class EmptyQueueEventListener(EventListener[EmptyQueueEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_empty_queue_event(self, event: EmptyQueueEvent):
        pass
