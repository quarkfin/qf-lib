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

import queue
import warnings
from typing import Dict, Type, Sequence

from qf_lib.backtesting.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.events.end_trading_event.end_trading_event import EndTradingEvent
from qf_lib.backtesting.events.event_base import Event, EventNotifier, EventListener
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

_EventType = Type[Event]


class EventManager:
    """
    Class which takes the event and passes it to all handlers which are "interested" in this type of event.
    Handlers can subscribe for the given event type, so that they will be notified each time when the event
    of this type occurs.
    """

    def __init__(self, timer: Timer) -> None:
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.events_queue = queue.Queue()  # type: queue.Queue
        self.timer = timer

        self.continue_trading = True
        """
        True if trading shall be continued (e.g. the backtest shall go on). False otherwise (e.g. no more data available
        for the backtest or the user terminated the backtest).
        """

        self._events_to_notifiers = {}  # type: Dict[_EventType, EventNotifier]
        """
        Mapping: event type to a corresponding notifier.
        """

    def register_notifiers(self, notifiers_list: Sequence[EventNotifier]):
        """
        Registers every notifier from the list of notifiers and associates them with certain types of events (defined
        by EventNotifier.events_type()). After being registered notifier can have listeners added to it.

        Next whenever event of type associated with the notifier occurs, event manager will tell the notifier
        to notify all its listeners.
        """
        for notifier in notifiers_list:
            self._events_to_notifiers[notifier.events_type()] = notifier

    def subscribe(self, event_type: _EventType, listener: EventListener):
        """
        Whenever the event of type event_type occurs, the listener should be notified.

        DEPRECATED
        """
        notifier = self._events_to_notifiers[event_type]
        notifier_type_name = str(type(notifier))
        warnings.warn(
            "EventManager.subscribe() is deprecated. Please use the {:s}.subscribe().".format(notifier_type_name),
            DeprecationWarning
        )
        notifier.subscribe(listener)

    def unsubscribe(self, event_type: _EventType, listener: EventListener):
        """
        Stop notifications of events' occurrences of type event_type.

        DEPRECATED
        """
        notifier = self._events_to_notifiers[event_type]
        notifier_type_name = str(type(notifier))
        warnings.warn(
            "EventManager.unsubscribe() is deprecated. Please use the {:s}.unsubscribe().".format(notifier_type_name),
            DeprecationWarning
        )
        notifier.unsubscribe(listener)

    def publish(self, event: Event):
        """
        Puts a new event in the event queue.
        """
        self.events_queue.put(event)

    def dispatch_next_event(self) -> None:
        """
        Takes next event from the events' queue and notifies proper handlers.

        Returns
        -------
        the dispatched event
        """
        event = self._get_next_event()
        self._dispatch_event(event)

    def _get_next_event(self):
        try:
            # this assumes that all components of a backtester are running in the same thread (no multi-threading)
            # Checking if queue is empty in this manner is not thread-safe.
            event = self.events_queue.get(block=False)
        except queue.Empty:
            event = EmptyQueueEvent()
        return event

    def _dispatch_event(self, event: Event):
        str_template = 'Dispatching event: {}'.format(event)
        self.logger.debug(str_template)

        event_type = type(event)

        if isinstance(event, TimeEvent):
            event_type = TimeEvent
        elif event_type == EndTradingEvent:
            self.continue_trading = False

        notifier = self._events_to_notifiers[event_type]
        notifier.notify_all(event)
