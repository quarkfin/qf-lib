from typing import Type

from qf_lib.backtesting.qstrader.events.event_base import EventNotifier
from qf_lib.backtesting.qstrader.events.price_events.price_event_notifier import PriceEventNotifier
from qf_lib.backtesting.qstrader.events.price_events.tick_event.tick_event import TickEvent
from qf_lib.backtesting.qstrader.events.price_events.tick_event.tick_event_listener import TickEventListener


class TickEventNotifier(EventNotifier[TickEvent, TickEventListener]):
    def __init__(self, price_event_notifier: PriceEventNotifier) -> None:
        super().__init__()
        self.price_event_notifier = price_event_notifier

    def notify_all(self, event: TickEvent):
        self.price_event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_tick_event(event)

    @classmethod
    def events_type(cls) -> Type[TickEvent]:
        return TickEvent
