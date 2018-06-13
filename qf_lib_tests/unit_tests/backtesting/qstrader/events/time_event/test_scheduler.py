import unittest
from datetime import datetime
from unittest import TestCase

from mockito import mock, when, verify, ANY

from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer


class TestScheduler(TestCase):
    class _CustomTimeEvent(TimeEvent):
        @classmethod
        def next_trigger_time(cls, now: datetime) -> datetime:
            return now + RelativeDelta(days=2)

        def notify(self, listener) -> None:
            listener.on_custom_time_event(self)

    class _AnotherCustomTimeEvent(TimeEvent):
        @classmethod
        def next_trigger_time(cls, now: datetime) -> datetime:
            return now + RelativeDelta(day=4)

        def notify(self, listener) -> None:
            listener.on_another_custom_time_event(self)

    def setUp(self):
        self.timer = SettableTimer()
        self.scheduler = Scheduler(self.timer)

    def test_get_next_time_event(self):
        listener = self._get_listeners_mock()

        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.timer.set_current_time(str_to_date("2018-01-01"))

        time_event = self.scheduler.get_next_time_event()
        self.assertEqual(str_to_date("2018-01-03"), time_event.time)

    def test_get_next_time_event_is_not_changing_state_of_scheduler(self):
        listener = self._get_listeners_mock()

        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.timer.set_current_time(str_to_date("2018-01-01"))

        self.scheduler.get_next_time_event()
        self.scheduler.get_next_time_event()
        time_event = self.scheduler.get_next_time_event()
        self.assertEqual(str_to_date("2018-01-03"), time_event.time)

    def test_correct_time_event_is_returned(self):
        self.timer.set_current_time(str_to_date("2018-01-01"))

        listener = self._get_listeners_mock()
        another_listener = self._get_listeners_mock()

        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.scheduler.subscribe(self._AnotherCustomTimeEvent, another_listener)

        actual_time_event = self.scheduler.get_next_time_event()
        expected_time_event = self._CustomTimeEvent(str_to_date("2018-01-03"))
        self.assertEqual(expected_time_event, actual_time_event)

        self.timer.set_current_time(str_to_date("2018-01-03"))
        another_actual_time_event = self.scheduler.get_next_time_event()
        another_expected_time_event = self._AnotherCustomTimeEvent(str_to_date("2018-01-04"))
        self.assertEqual(another_expected_time_event, another_actual_time_event)

    def test_callback_method_called(self):
        self.timer.set_current_time(str_to_date("2018-01-01"))

        # create custom time events of two kinds
        custom_event_1 = self._CustomTimeEvent(str_to_date("2018-01-03"))
        custom_event_2 = self._CustomTimeEvent(str_to_date("2018-01-05"))
        another_custom_event_1 = self._AnotherCustomTimeEvent(str_to_date("2018-01-04"))
        another_custom_event_2 = self._AnotherCustomTimeEvent(str_to_date("2018-01-05"))
        another_custom_event_3 = self._AnotherCustomTimeEvent(str_to_date("2018-01-06"))

        # create listener's mock
        listener = mock(strict=True)
        when(listener).on_custom_time_event(custom_event_1)
        when(listener).on_custom_time_event(custom_event_2)

        # create another listener's mock
        another_listener = mock(strict=True)
        when(another_listener).on_another_custom_time_event(another_custom_event_1)
        when(another_listener).on_another_custom_time_event(another_custom_event_2)
        when(another_listener).on_another_custom_time_event(another_custom_event_3)

        # subscribe listeners to corresponding time events
        self.scheduler.subscribe(self._CustomTimeEvent, listener)
        self.scheduler.subscribe(self._AnotherCustomTimeEvent, another_listener)

        # test behaviour
        self.scheduler.notify_all(custom_event_1)
        verify(listener).on_custom_time_event(custom_event_1)

        self.scheduler.notify_all(another_custom_event_1)
        verify(another_listener).on_another_custom_time_event(another_custom_event_1)

        self.scheduler.notify_all(custom_event_2)
        verify(listener).on_custom_time_event(custom_event_2)

        self.scheduler.notify_all(another_custom_event_2)
        verify(another_listener).on_another_custom_time_event(another_custom_event_2)

        self.scheduler.notify_all(another_custom_event_3)
        verify(another_listener).on_another_custom_time_event(another_custom_event_3)

    @staticmethod
    def _get_listeners_mock():
        listener = mock(strict=True)
        when(listener).on_custom_time_event(ANY(TimeEvent))

        return listener


if __name__ == '__main__':
    unittest.main()
