from typing import Type

from qf_lib.backtesting.qstrader.events.event_base import EventNotifier, AllEventNotifier
from qf_lib.backtesting.qstrader.events.price_events.price_event import PriceEvent
from qf_lib.backtesting.qstrader.events.price_events.price_event_listener import PriceEventListener


class PriceEventNotifier(EventNotifier[PriceEvent, PriceEventListener]):
    def __init__(self, event_notifier: AllEventNotifier) -> None:
        super().__init__()
        self.event_notifier = event_notifier

    def notify_all(self, event: PriceEvent):
        self.event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_price_event(event)

    @classmethod
    def events_type(cls) -> Type[PriceEvent]:
        return PriceEvent
