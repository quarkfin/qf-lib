import abc
from datetime import datetime


class Timer(object):
    """
    Timer object which is a component in IOC. Used for getting information about time.
    """

    @abc.abstractmethod
    def now(self) -> datetime:
        pass


class RealTimer(Timer):
    """
    Timer which gives the real current time.
    """
    def now(self) -> datetime:
        return datetime.now()


class SettableTimer(Timer):
    """
    Timer object which doesn't give the real current time, but is "faking" it (current time can be set).
    """
    def __init__(self, initial_time: datetime = None):
        self.time = initial_time

    def now(self) -> datetime:
        return self.time

    def set_current_time(self, time: datetime):
        self.time = time
