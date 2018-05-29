from typing import Type

from qf_lib.backtesting.qstrader.events.event_base import EventNotifier, AllEventNotifier
from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent
from qf_lib.backtesting.qstrader.events.fill_event.fill_event_listener import FillEventListener


class FillEventNotifier(EventNotifier[FillEvent, FillEventListener]):
    def __init__(self, event_notifier: AllEventNotifier) -> None:
        super().__init__()
        self.event_notifier = event_notifier

    def notify_all(self, event: FillEvent):
        self.event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_fill_event(event)

    @classmethod
    def events_type(cls) -> Type[FillEvent]:
        return FillEvent
