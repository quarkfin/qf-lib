from typing import Type

from qf_lib.backtesting.qstrader.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.qstrader.events.empty_queue_event.empty_queue_event_listener import EmptyQueueEventListener
from qf_lib.backtesting.qstrader.events.event_base import EventNotifier, AllEventNotifier


class EmptyQueueEventNotifier(EventNotifier[EmptyQueueEvent, EmptyQueueEventListener]):
    def __init__(self, event_notifier: AllEventNotifier) -> None:
        super().__init__()
        self.event_notifier = event_notifier

    def notify_all(self, event: EmptyQueueEvent):
        self.event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_empty_queue_event(event)

    @classmethod
    def events_type(cls) -> Type[EmptyQueueEvent]:
        return EmptyQueueEvent
