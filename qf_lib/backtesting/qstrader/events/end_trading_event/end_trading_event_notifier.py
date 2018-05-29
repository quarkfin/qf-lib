from typing import Type

from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event import EndTradingEvent
from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event_listener import EndTradingEventListener
from qf_lib.backtesting.qstrader.events.event_base import EventNotifier, AllEventNotifier


class EndTradingEventNotifier(EventNotifier[EndTradingEvent, EndTradingEventListener]):
    def __init__(self, event_notifier: AllEventNotifier) -> None:
        super().__init__()
        self.event_notifier = event_notifier

    def notify_all(self, event: EndTradingEvent):
        self.event_notifier.notify_all(event)

        for listener in self.listeners:
            listener.on_end_trading_event(event)

    @classmethod
    def events_type(cls) -> Type[EndTradingEvent]:
        return EndTradingEvent
