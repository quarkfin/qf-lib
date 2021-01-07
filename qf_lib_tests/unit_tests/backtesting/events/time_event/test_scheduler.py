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

import unittest
from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock

from qf_lib.backtesting.events.time_event.periodic_event.periodic_event import PeriodicEvent
from qf_lib.backtesting.events.time_event.single_time_event.single_time_event import SingleTimeEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer


class TestScheduler(TestCase):
    class _CustomTimeEvent(TimeEvent):
        def next_trigger_time(self, now: datetime) -> datetime:
            return now + RelativeDelta(days=2)

        def notify(self, listener) -> None:
            listener.on_custom_time_event(self)

    class _AnotherCustomTimeEvent(TimeEvent):
        def next_trigger_time(self, now: datetime) -> datetime:
            return now + RelativeDelta(day=4)

        def notify(self, listener) -> None:
            listener.on_another_custom_time_event(self)

    class PeriodicEvent15Minutes(PeriodicEvent):
        frequency = Frequency.MIN_15
        start_time = {"hour": 9, "minute": 45, "second": 0}
        end_time = {"hour": 11, "minute": 15, "second": 0}

        def notify(self, _) -> None:
            pass

    class PeriodicEvent30Minutes(PeriodicEvent):
        frequency = Frequency.MIN_30
        start_time = {"hour": 9, "minute": 30, "second": 0}
        end_time = {"hour": 10, "minute": 30, "second": 0}

        def notify(self, _) -> None:
            pass

    def setUp(self):
        self.timer = SettableTimer()
        self.scheduler = Scheduler(self.timer)

    def test_get_next_time_event(self):
        listener = Mock()
        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.timer.set_current_time(str_to_date("2018-01-01"))

        time_events_list, time = self.scheduler.get_next_time_events()
        self.assertEqual(str_to_date("2018-01-03"), time)

    def test_get_multiple_next_time_events(self):
        listener = Mock()

        self.timer.set_current_time(str_to_date("2018-01-01"))
        self.scheduler.subscribe(self._AnotherCustomTimeEvent, listener)

        self.timer.set_current_time(str_to_date("2018-01-02"))
        self.scheduler.subscribe(self._CustomTimeEvent, listener)

        time_events_list, time = self.scheduler.get_next_time_events()
        expected_time_events = [
            self._CustomTimeEvent(),
            self._AnotherCustomTimeEvent()
        ]

        self.assertCountEqual(time_events_list, expected_time_events)

    def test_get_next_time_event_is_not_changing_state_of_scheduler(self):
        listener = Mock()

        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.timer.set_current_time(str_to_date("2018-01-01"))

        self.scheduler.get_next_time_events()
        self.scheduler.get_next_time_events()
        time_events_list, time = self.scheduler.get_next_time_events()
        self.assertEqual(str_to_date("2018-01-03"), time)

    def test_correct_time_event_is_returned(self):
        self.timer.set_current_time(str_to_date("2018-01-01"))

        listener = Mock()
        another_listener = Mock()

        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.scheduler.subscribe(self._AnotherCustomTimeEvent, another_listener)

        actual_time_events_list, time = self.scheduler.get_next_time_events()
        expected_time_event = self._CustomTimeEvent()
        self.assertIn(expected_time_event, actual_time_events_list)

        self.timer.set_current_time(str_to_date("2018-01-03"))
        another_actual_time_events_list, time = self.scheduler.get_next_time_events()
        another_expected_time_event = self._AnotherCustomTimeEvent()
        self.assertIn(another_expected_time_event, another_actual_time_events_list)

    def test_callback_method_called(self):
        self.timer.set_current_time(str_to_date("2018-01-01"))

        # create custom time events of two kinds
        custom_event = self._CustomTimeEvent()
        another_custom_event = self._AnotherCustomTimeEvent()

        listener = Mock()
        another_listener = Mock()

        # subscribe listeners to corresponding time events
        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.scheduler.subscribe(self._AnotherCustomTimeEvent, another_listener)

        # test behaviour
        self.scheduler.notify_all(custom_event)

        listener.on_custom_time_event.assert_called_once()

        self.scheduler.notify_all(another_custom_event)
        another_listener.on_another_custom_time_event.assert_called_once()

    def test_get_next_time_event_single_time_events(self):
        self.timer.set_current_time(str_to_date("2018-01-02 10:00:00.000000", DateFormat.FULL_ISO))

        listener = Mock()
        self.scheduler.subscribe(SingleTimeEvent, listener)

        trigger_time = str_to_date("2018-01-02 13:00:00.000000", DateFormat.FULL_ISO)
        SingleTimeEvent.schedule_new_event(trigger_time, {})

        time_events_list, time = self.scheduler.get_next_time_events()
        self.assertEqual(trigger_time, time)

    def test_get_next_time_event_periodic_events(self):
        self.timer.set_current_time(str_to_date("2018-01-01 10:00:00.000000", DateFormat.FULL_ISO))

        listener = Mock()

        self.scheduler.subscribe(self.PeriodicEvent15Minutes, listener)
        self.scheduler.subscribe(self.PeriodicEvent30Minutes, listener)

        # There will be exactly one event scheduled for 10:15:00
        time_events_list, time = self.scheduler.get_next_time_events()
        self.assertEqual(str_to_date("2018-01-01 10:15:00.000000", DateFormat.FULL_ISO), time)
        self.assertEqual(1, len(time_events_list))

        self.timer.set_current_time(str_to_date("2018-01-01 10:15:00.000000", DateFormat.FULL_ISO))

        # There will be two events scheduled for 10:30:00
        time_events_list, time = self.scheduler.get_next_time_events()
        self.assertEqual(str_to_date("2018-01-01 10:30:00.000000", DateFormat.FULL_ISO), time)
        self.assertEqual(2, len(time_events_list))

    def test_get_next_time_event_periodic_and_single_time_events(self):
        self.timer.set_current_time(str_to_date("2018-01-01 10:00:00.000000", DateFormat.FULL_ISO))

        listener_periodic = Mock()
        listener_single = Mock()

        self.scheduler.subscribe(self.PeriodicEvent15Minutes, listener_periodic)
        self.scheduler.subscribe(SingleTimeEvent, listener_single)

        trigger_time = str_to_date("2018-01-01 10:15:00.000000", DateFormat.FULL_ISO)
        SingleTimeEvent.schedule_new_event(trigger_time, {})

        # There will be two events scheduled for 10:15:00
        time_events_list, time = self.scheduler.get_next_time_events()
        self.assertEqual(str_to_date("2018-01-01 10:15:00.000000", DateFormat.FULL_ISO), time)
        self.assertEqual(2, len(time_events_list))

        time_events_list_types = [type(event) for event in time_events_list]
        self.assertCountEqual(time_events_list_types, [self.PeriodicEvent15Minutes, SingleTimeEvent])


if __name__ == '__main__':
    unittest.main()
