from abc import ABCMeta, abstractmethod

from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class RegularTimeEvent(TimeEvent, metaclass=ABCMeta):
    """ TimeEvent which occurrs on regular basis (e.g. each day at 17:00). """

    @classmethod
    @abstractmethod
    def trigger_time(cls) -> RelativeDelta:
        """
        Returns the RelativeDelta which describes at what time the RegularTimeEvent occurrs
        (e.g. RelativeDelta(hour=16, minute=0, second=0, milisecond=0) for an event which occurrs every day at 16:00).
        """
        pass
