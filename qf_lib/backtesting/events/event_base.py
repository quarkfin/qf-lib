#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import abc
from typing import Generic, TypeVar, Set, Type


class Event(object, metaclass=abc.ABCMeta):
    """
    Event is base class providing an interface for all subsequent
    (inherited) events, that will trigger further events in the
    trading infrastructure.
    """

    def __str__(self):
        return "{:<25}".format(self.__class__.__name__)


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
        """
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
