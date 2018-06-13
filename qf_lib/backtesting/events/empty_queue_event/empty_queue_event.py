import datetime

from qf_lib.backtesting.events.event_base import Event


class EmptyQueueEvent(Event):
    """
    Indicates that there are no more events in the queue.
    """
    def __init__(self, time: datetime.datetime) -> None:
        super().__init__(time)
