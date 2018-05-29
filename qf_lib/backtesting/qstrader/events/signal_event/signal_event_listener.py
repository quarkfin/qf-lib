import abc

from qf_lib.backtesting.qstrader.events.event_base import EventListener
from qf_lib.backtesting.qstrader.events.signal_event.signal_event import SignalEvent


class SignalEventListener(EventListener[SignalEvent], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on_signal_event(self, event: SignalEvent):
        pass
