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
import datetime
from typing import List, Tuple
from unittest import TestCase

from qf_lib.backtesting.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.events.empty_queue_event.empty_queue_event_listener import EmptyQueueEventListener
from qf_lib.backtesting.events.end_trading_event.end_trading_event import EndTradingEvent
from qf_lib.backtesting.events.end_trading_event.end_trading_event_listener import EndTradingEventListener
from qf_lib.backtesting.events.event_base import AllEventListener, Event
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.events.time_event.periodic_event.periodic_event import PeriodicEvent
from qf_lib.backtesting.events.time_event.regular_time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.single_time_event.single_time_event import SingleTimeEvent
from qf_lib.backtesting.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer, Timer
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class PeriodicEvent1Hour(PeriodicEvent):
    frequency = Frequency.MIN_60
    start_time = {"hour": 13, "minute": 45, "second": 0}
    end_time = {"hour": 14, "minute": 45, "second": 0}

    def notify(self, listener):
        listener.on_new_bar(self)


class DummyListener(AllEventListener, EmptyQueueEventListener, EndTradingEventListener):
    """
    A "driver" class used for the integration test. It simulates the behavior of a Strategy,
    ExecutionHandler and it also ends the simulation (when the BeforeMarketOpenEvent occurs for the second time).
    """

    def __init__(self, notifiers: Notifiers, event_manager: EventManager, timer: Timer):
        self.registered_events = []  # type: List[Tuple[Event, datetime]]
        self.registered_single_time_events = {}

        self.event_manager = event_manager
        self.timer = timer

        notifiers.empty_queue_event_notifier.subscribe(self)
        notifiers.end_trading_event_notifier.subscribe(self)
        notifiers.scheduler.subscribe(MarketOpenEvent, self)
        notifiers.scheduler.subscribe(AfterMarketCloseEvent, self)
        notifiers.scheduler.subscribe(MarketCloseEvent, self)
        notifiers.scheduler.subscribe(PeriodicEvent1Hour, self)
        notifiers.scheduler.subscribe(SingleTimeEvent, self)

    def on_empty_queue_event(self, event: EmptyQueueEvent):
        self._register_event(event)

    def on_end_trading_event(self, event: EndTradingEvent):
        self._register_event(event)

    def on_market_open(self, event: MarketOpenEvent):
        self._register_event(event)

    def on_after_market_close(self, event: AfterMarketCloseEvent):
        self._register_event(event)

    def on_market_close(self, event: MarketCloseEvent):
        self._register_event(event)

    def on_single_time_event(self, event: SingleTimeEvent):
        self.registered_single_time_events[self.timer.now()] = event.get_data(self.timer.now())
        self._register_event(event)

    def on_new_bar(self, event: PeriodicEvent):
        # Schedule new single time event, in 5 minutes from now with the time of scheduling
        # passed as data parameter
        current_time = self.timer.now()
        SingleTimeEvent.schedule_new_event(current_time + RelativeDelta(minutes=5), data=current_time)
        self._register_event(event)

    def _register_event(self, event: Event) -> None:
        self.registered_events.append((event, self.timer.now()))


class TestEventManagement(TestCase):
    """
    Tests the interaction among: EventManager, notifiers (including Scheduler) and the BacktestTimeFlowController.
    Tests:
    - if events are published correctly,
    - if corresponding listeners are notified of events in the right order,
    - if BacktestTimeFlowController creates TimeEvents at proper time.
    """

    def setUp(self):
        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})
        AfterMarketCloseEvent.set_trigger_time({"hour": 21, "minute": 0, "second": 0, "microsecond": 0})

    def test_event_management(self):
        timer = SettableTimer(initial_time=str_to_date("2018-04-10 00:00:00.000000", DateFormat.FULL_ISO))
        end_date = str_to_date("2018-04-10")

        notifiers = Notifiers(timer)
        event_manager = self._create_event_manager(timer, notifiers)
        BacktestTimeFlowController(
            notifiers.scheduler, event_manager, timer, notifiers.empty_queue_event_notifier, end_date
        )

        listener = DummyListener(notifiers, event_manager, timer)

        last_event = None
        while not isinstance(last_event, EndTradingEvent):
            event_manager.dispatch_next_event()
            last_event, _ = listener.registered_events[-1]

        expected_events = [
            (EmptyQueueEvent, str_to_date("2018-04-10 08:00:00.000000", DateFormat.FULL_ISO)),
            (MarketOpenEvent, str_to_date("2018-04-10 13:30:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 13:45:00.000000", DateFormat.FULL_ISO)),
            (PeriodicEvent1Hour, str_to_date("2018-04-10 13:45:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 13:50:00.000000", DateFormat.FULL_ISO)),
            (SingleTimeEvent, str_to_date("2018-04-10 13:50:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 14:45:00.000000", DateFormat.FULL_ISO)),
            (PeriodicEvent1Hour, str_to_date("2018-04-10 14:45:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 14:50:00.000000", DateFormat.FULL_ISO)),
            (SingleTimeEvent, str_to_date("2018-04-10 14:50:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 20:00:00.000000", DateFormat.FULL_ISO)),
            (MarketCloseEvent, str_to_date("2018-04-10 20:00:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 21:00:00.000000", DateFormat.FULL_ISO)),
            (AfterMarketCloseEvent, str_to_date("2018-04-10 21:00:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 21:00:00.000000", DateFormat.FULL_ISO)),
            (EndTradingEvent, str_to_date("2018-04-10 21:00:00.000000", DateFormat.FULL_ISO)),
        ]

        expected_events = [type_of_event for type_of_event, time in expected_events]
        actual_events = [type(event) for event, time in listener.registered_events]

        assert_lists_equal(expected_events, actual_events, absolute_tolerance=0.0)

        expected_single_time_events_data = {
            str_to_date("2018-04-10 13:50:00.000000", DateFormat.FULL_ISO):
                str_to_date("2018-04-10 13:45:00.000000", DateFormat.FULL_ISO),
            str_to_date("2018-04-10 14:50:00.000000", DateFormat.FULL_ISO):
                str_to_date("2018-04-10 14:45:00.000000", DateFormat.FULL_ISO)
        }

        for key in expected_single_time_events_data:
            self.assertEqual(expected_single_time_events_data[key], listener.registered_single_time_events[key])

    def _create_event_manager(self, timer, notifiers):
        event_manager = EventManager(timer)

        event_manager.register_notifiers([
            notifiers.empty_queue_event_notifier,
            notifiers.end_trading_event_notifier,
            notifiers.scheduler
        ])
        return event_manager
