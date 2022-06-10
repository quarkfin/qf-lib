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
import operator
from datetime import datetime
from typing import Dict, Type, TypeVar, List, Any, Generator, Tuple

from qf_lib.backtesting.events.time_event.periodic_event.intraday_bar_event import IntradayBarEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.single_time_event.schedule_order_execution_event import \
    ScheduleOrderExecutionEvent
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

ConcreteTimeEvent = TypeVar('TimeEventType', bound=TimeEvent)
TypeOfEvent = Type[ConcreteTimeEvent]


class Scheduler:
    """
    Class responsible for generating TimeEvents. Using this class listeners can subscribe to concrete TimeEvents
    (e.g. MarketOpenEvent) and they will be notified whenever this event is generated.

    Normally time events are generated whenever the EventManager's queue is empty. The generation will be triggered
    by TimeFlowController.
    """

    def __init__(self, timer: Timer):
        self.timer = timer
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self._time_event_type_to_subscribers = {}  # type: Dict[TypeOfEvent, List[Any]]
        self._time_event_type_to_object = {}

    @classmethod
    def events_type(cls):
        return TimeEvent

    def subscribe(self, type_of_time_event: TypeOfEvent, listener) -> None:
        """
        Subscribes listener to a certain type of TimeEvent (e.g. MarketOpenEvent, PeriodicEvent). Listener will be only
        notified of events of this concrete type (not all TimeEvents like with event_manager.subscribe(TimeEvent, self)).

        Parameters
        ----------
        type_of_time_event
            concrete type of TimeEvent (e.g. MarketOpenEvent)
        listener
            listener to the concrete type of TimeEvent. It needs to have a proper callback method (defined in
            TimeEvent.notify() method).
        """
        listeners = self._time_event_type_to_subscribers.get(type_of_time_event, [])

        if len(listeners) == 0:
            self._time_event_type_to_subscribers[type_of_time_event] = listeners

        listeners.append(listener)

        # Check if it is necessary to initialize a new object of type_of_time_event type
        if type_of_time_event not in self._time_event_type_to_object.keys():
            self._time_event_type_to_object[type_of_time_event] = type_of_time_event()

    def get_next_time_events(self) -> Tuple[List[ConcreteTimeEvent], datetime]:
        """
        Finds the TimeEvents which should be triggered soonest and returns a list of them. All the returned TimeEvents
        are scheduled for the exactly same time.
        The order of the simultaneously executed TimeEvents is as follows:
            1. At first, all scheduled ScheduleOrderExecutionEvents are executed
            2. Secondly, all IntradayBarEvents, MarketOpenEvents and MarketCloseEvents are executed
            3. Next, all other events are scheduled.
        Ordering all ScheduleOrderExecutionEvents before the IntradayBarEvents, MarketOpenEvents and MarketCloseEvents
        ensures that, when a new bar is received and the orders will be executed, all orders scheduled for this certain
        time will be already processed and accepted.
        """
        now = self.timer.now()

        times_and_events = [
            (time_event.next_trigger_time(now), time_event) for time_event in self._time_event_type_to_object.values()
            if time_event.next_trigger_time(now) is not None
        ]  # type: Generator[Tuple[datetime, ConcreteTimeEvent]]

        next_trigger_time, _ = min(times_and_events, key=operator.itemgetter(0))  # type: datetime

        next_time_events = [event for time, event in times_and_events if time == next_trigger_time]
        # type: List[ConcreteTimeEvent]

        time_events_priority = {
            ScheduleOrderExecutionEvent: 0,
            IntradayBarEvent: 1,
            MarketOpenEvent: 1,
            MarketCloseEvent: 1
        }

        next_time_events.sort(key=lambda ev: time_events_priority.get(type(ev), float('inf')))
        return next_time_events, next_trigger_time

    def notify_all(self, time_event: ConcreteTimeEvent):
        """
        Notifies each listener of the occurrence of the given concrete event.
        """

        time_event_type = type(time_event)
        listeners = self._time_event_type_to_subscribers.get(time_event_type, [])

        if len(listeners) == 0:
            self.logger.warning("No listeners for time event of type: {:s}", str(time_event_type))

        for listener in listeners:
            time_event.notify(listener)
