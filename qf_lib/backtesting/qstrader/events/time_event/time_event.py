from abc import abstractmethod, ABCMeta
from datetime import datetime

from qf_lib.backtesting.qstrader.events.event_base import Event


class TimeEvent(Event, metaclass=ABCMeta):
    """
    Represents an event associated with certain date/time (e.g. 2017-05-13 13:00).
    """

    @classmethod
    @abstractmethod
    def next_trigger_time(cls, now: datetime) -> datetime:
        pass

    @abstractmethod
    def notify(self, listener) -> None:
        pass

    def __eq__(self, other):
        if self is other:
            return True

        if type(self) != type(other):
            return False

        return self.time == other.time

    def __hash__(self):
        return hash((type(self), self.time))
