import abc
from datetime import datetime
from typing import Generic, TypeVar, Set, Type, Optional

from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class Event(object, metaclass=abc.ABCMeta):
    """
    Event is base class providing an interface for all subsequent
    (inherited) events, that will trigger further events in the
    trading infrastructure.
    """

    def __init__(self, time: Optional[datetime]):
        self.time = time

    def __str__(self):
        return "{} - {:<25}".format(self.time, self.__class__.__name__)


_EventSubclass = TypeVar('_EventSubclass', bound=Event)


class EventListener(Generic[_EventSubclass], metaclass=abc.ABCMeta):
    """
    Abstract class for all objects which react to occurrences of certain type of events (type of events declared
    as classes' parameter).
    """
    pass


_EventListenerSubclass = TypeVar('_EventListenerSubclass', bound=EventListener)


class EventNotifier(Generic[_EventSubclass, _EventListenerSubclass], metaclass=abc.ABCMeta):
    """
    Class used for notifying all listeners of given type of event that it occurred.
    """

    def __init__(self):
        self.listeners = set()  # type: Set[_EventListenerSubclass]

    def subscribe(self, listener: EventListener):
        """
        Subscribe to events of the EventNotifier.events_type()
        """
        self.listeners.add(listener)

    def unsubscribe(self, listener: EventListener):
        """"
        Stop notifications of events' occurrences for the given listener.
        """
        self.listeners.remove(listener)

    @abc.abstractmethod
    def notify_all(self, event: _EventSubclass) -> None:
        """
        Notifies all the listeners about the event occurred.

        Parameters
        ----------
        event
            event about all the listeners should be notified
        """
        pass

    @classmethod
    @abc.abstractmethod
    def events_type(cls) -> Type[_EventSubclass]:
        pass


class AllEventListener(EventListener[Event], metaclass=abc.ABCMeta):
    def on_event(self, event: Event):
        pass


class AllEventNotifier(EventNotifier[Event, AllEventListener]):
    def notify_all(self, event: Event):
        for listener in self.listeners:
            listener.on_event(event)

    @classmethod
    def events_type(cls) -> Type[Event]:
        return Event
