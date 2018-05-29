from typing import Type

from qf_lib.backtesting.qstrader.events.event_base import EventNotifier
from qf_lib.backtesting.qstrader.events.price_events.bar_event.bar_event import BarEvent
from qf_lib.backtesting.qstrader.events.price_events.bar_event.bar_event_listener import BarEventListener
from qf_lib.backtesting.qstrader.events.price_events.price_event_notifier import PriceEventNotifier


class BarEventNotifier(EventNotifier[BarEvent, BarEventListener]):
    def __init__(self, price_event_notifier: PriceEventNotifier) -> None:
        super().__init__()
        self.price_event_notifier = price_event_notifier

    def notify_all(self, event: BarEvent):
        self.price_event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_bar_event(event)

    @classmethod
    def events_type(cls) -> Type[BarEvent]:
        return BarEvent
