import abc

from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event import EndTradingEvent
from qf_lib.backtesting.qstrader.events.event_base import EventListener


class EndTradingEventListener(EventListener[EndTradingEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_end_trading_event(self, event: EndTradingEvent):
        pass
