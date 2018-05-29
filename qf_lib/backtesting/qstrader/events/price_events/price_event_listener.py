import abc

from qf_lib.backtesting.qstrader.events.event_base import EventListener
from qf_lib.backtesting.qstrader.events.price_events.price_event import PriceEvent


class PriceEventListener(EventListener[PriceEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_price_event(self, event: PriceEvent):
        pass
