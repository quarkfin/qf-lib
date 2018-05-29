from typing import Type

from qf_lib.backtesting.qstrader.events.event_base import EventNotifier, AllEventNotifier
from qf_lib.backtesting.qstrader.events.signal_event.signal_event import SignalEvent
from qf_lib.backtesting.qstrader.events.signal_event.signal_event_listener import SignalEventListener


class SignalEventNotifier(EventNotifier[SignalEvent, SignalEventListener]):
    def __init__(self, event_notifier: AllEventNotifier) -> None:
        super().__init__()
        self.event_notifier = event_notifier

    def notify_all(self, event: SignalEvent):
        self.event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_signal_event(event)

    @classmethod
    def events_type(cls) -> Type[SignalEvent]:
        return SignalEvent
