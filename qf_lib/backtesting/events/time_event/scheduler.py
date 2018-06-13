from datetime import datetime
from typing import Dict, Type, TypeVar, List, Any, Generator, Tuple

from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

ConcreteTimeEvent = TypeVar('TimeEventType', bound=TimeEvent)
TypeOfEvent = Type[ConcreteTimeEvent]


class Scheduler(object):
    """
    Class responsible for generating TimeEvents. Using this class listeners can subscribe to concrete TimeEvents
    (e.g. MarketOpenEvent) and they will be notified whenever this event is generated.

    Normally time events are generated whenever the EventManager's queue is empty. The generation will be triggered
    by TimeFlowController.

    One should not use Scheduler for subscribing to all TimeEvents. If you want to subscribe to all TimeEvents then
    use EventManager.subscribe(...) method.
    """

    def __init__(self, timer: Timer):
        self.timer = timer
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self._time_event_to_subscribers = {}  # type: Dict[TypeOfEvent, List[Any]]

    @classmethod
    def events_type(cls):
        return TimeEvent

    def subscribe(self, type_of_time_event: TypeOfEvent, listener) -> None:
        """
        Subscribes listener to a concrete TimeEvent (e.g. MarketOpenEvent). Listener will be only notified
        of events of this concrete type (not all TimeEvents like with event_manager.subscribe(TimeEvent, self).

        If you want to subscribe to all TimeEvents, use EventManager.subscribe(TimeEvent) method.

        Parameters
        ----------
        type_of_time_event
            concrete type of TimeEvent (e.g. MarketOpenEvent)
        listener
            listener to the concrete type of TimeEvent. It needs to have a proper callback method (defined in
            TimeEvent.notify() method).
        """
        listeners = self._time_event_to_subscribers.get(type_of_time_event, [])

        if len(listeners) == 0:
            self._time_event_to_subscribers[type_of_time_event] = listeners

        listeners.append(listener)

    def get_next_time_event(self) -> ConcreteTimeEvent:
        """
        Finds the TimeEvent which should be triggered soonest and returns it.
        """
        now = self.timer.now()

        times_and_event_types = (
            (time_event.next_trigger_time(now), time_event) for time_event in self._time_event_to_subscribers
        )  # type: Generator[Tuple[datetime, TypeOfEvent]]
        next_trigger_time, time_event_type = min(times_and_event_types)  # type: Tuple[datetime, TypeOfEvent]

        return time_event_type(next_trigger_time)

    def notify_all(self, time_event: ConcreteTimeEvent):
        """
        Notifies each listener of the occurrence of the given concrete event.
        """

        time_event_type = type(time_event)
        listeners = self._time_event_to_subscribers.get(time_event_type, [])

        if len(listeners) == 0:
            self.logger.warning("No listeners for time event of type: {:s}", str(time_event_type))

        for listener in listeners:
            time_event.notify(listener)
