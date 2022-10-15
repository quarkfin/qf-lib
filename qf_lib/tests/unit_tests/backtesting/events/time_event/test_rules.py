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
from unittest import TestCase

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.single_time_event.single_time_event import SingleTimeEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.periodic_event.periodic_event import PeriodicEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date, DateFormat
from qf_lib.common.utils.dateutils.timer import SettableTimer


class TestRules(TestCase):

    def setUp(self):
        self.timer = SettableTimer()
        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    def test_market_open_rule(self):

        market_open_event = MarketOpenEvent()
        self.timer.set_current_time(str_to_date("2018-01-01 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_open_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-01 13:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        self.timer.set_current_time(str_to_date("2018-01-01 09:29:59.999999", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_open_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-01 13:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        self.timer.set_current_time(str_to_date("2018-01-01 13:30:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_open_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-02 13:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

    def test_exclude_weekends__market_open(self):
        market_open_event = MarketOpenEvent()
        market_open_event.exclude_weekends()

        # 11th of June 2022 is a Saturday
        self.timer.set_current_time(str_to_date("2022-06-11 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_open_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 13:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        # 12th of June 2022 is a Sunday
        self.timer.set_current_time(str_to_date("2022-06-12 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_open_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 13:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        # 13th of June 2022 is a Monday
        self.timer.set_current_time(str_to_date("2022-06-13 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_open_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 13:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

    def test_exclude_weekends__market_close(self):
        market_close_event = MarketCloseEvent()
        market_close_event.exclude_weekends()

        # 11th of June 2022 is a Saturday
        self.timer.set_current_time(str_to_date("2022-06-11 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_close_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 20:00:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        # 12th of June 2022 is a Sunday
        self.timer.set_current_time(str_to_date("2022-06-12 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_close_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 20:00:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        # 13th of June 2022 is a Monday
        self.timer.set_current_time(str_to_date("2022-06-13 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = market_close_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 20:00:00.000000", DateFormat.FULL_ISO), next_trigger_time)

    def test_periodic_events(self):
        self.timer.set_current_time(str_to_date("2018-01-01 13:23:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()

        class MinuteBarEvent(PeriodicEvent):
            frequency = Frequency.MIN_1
            start_time = {"hour": 8, "minute": 0, "second": 0}
            end_time = {"hour": 16, "minute": 0, "second": 0}

            def notify(self, listener):
                pass

        class Minutes15BarEvent(PeriodicEvent):
            frequency = Frequency.MIN_15
            start_time = {"hour": 8, "minute": 0, "second": 0}
            end_time = {"hour": 16, "minute": 0, "second": 0}

            def notify(self, listener):
                pass

        self.assertEqual(now + RelativeDelta(minutes=1), MinuteBarEvent().next_trigger_time(now))
        self.assertEqual(now + RelativeDelta(minute=30), Minutes15BarEvent().next_trigger_time(now))

        self.timer.set_current_time(str_to_date("2018-01-01 23:23:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()

        start_time = str_to_date("2018-01-02 08:00:00.000000", DateFormat.FULL_ISO)
        self.assertEqual(start_time, MinuteBarEvent().next_trigger_time(now))
        self.assertEqual(start_time, Minutes15BarEvent().next_trigger_time(now))

    def test_periodic_events_short_time_range(self):
        self.timer.set_current_time(str_to_date("2018-01-01 9:30:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()

        class Periodic15MinutesEvent(PeriodicEvent):
            frequency = Frequency.MIN_15
            start_time = {"hour": 9, "minute": 45, "second": 0}
            end_time = {"hour": 10, "minute": 10, "second": 0}

            def notify(self, listener):
                pass

        periodic_15_minutes_event = Periodic15MinutesEvent()

        now = periodic_15_minutes_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-01 9:45:00.000000", DateFormat.FULL_ISO), now)

        now = periodic_15_minutes_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-01 10:00:00.000000", DateFormat.FULL_ISO), now)

        now = periodic_15_minutes_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-02 9:45:00.000000", DateFormat.FULL_ISO), now)

    def test_exclude_weekends__periodic_event(self):
        class Periodic15MinutesEvent(PeriodicEvent):
            frequency = Frequency.MIN_15
            start_time = {"hour": 9, "minute": 45, "second": 0}
            end_time = {"hour": 10, "minute": 0, "second": 0}

            def notify(self, listener):
                pass

        # initiation must be after setting the exclude_weekends because of the PeriodicEvnet _events_list attribute
        Periodic15MinutesEvent.exclude_weekends()
        periodic_event = Periodic15MinutesEvent()

        # 11th of June 2022 is a Saturday
        self.timer.set_current_time(str_to_date("2022-06-11 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = periodic_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 09:45:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        # 12th of June 2022 is a Sunday
        self.timer.set_current_time(str_to_date("2022-06-12 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = periodic_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 09:45:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        # 13th of June 2022 is a Monday
        self.timer.set_current_time(str_to_date("2022-06-13 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = periodic_event.next_trigger_time(now)
        self.assertEqual(str_to_date("2022-06-13 09:45:00.000000", DateFormat.FULL_ISO), next_trigger_time)

    def test_single_time_events(self):
        self.timer.set_current_time(str_to_date("2018-01-01 13:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()

        # Schedule a few new events
        date_times = (
            str_to_date("2018-01-01 13:15:00.000000", DateFormat.FULL_ISO),
            str_to_date("2018-01-01 13:30:00.000000", DateFormat.FULL_ISO),
            str_to_date("2018-01-01 13:45:00.000000", DateFormat.FULL_ISO),
            str_to_date("2018-01-01 12:45:00.000000", DateFormat.FULL_ISO)
        )

        for date_time in date_times:
            SingleTimeEvent.schedule_new_event(date_time, None)

        self.assertEqual(str_to_date("2018-01-01 13:15:00.000000", DateFormat.FULL_ISO),
                         SingleTimeEvent().next_trigger_time(now))

        self.timer.set_current_time(SingleTimeEvent().next_trigger_time(now))
        now = self.timer.now()

        self.assertEqual(str_to_date("2018-01-01 13:30:00.000000", DateFormat.FULL_ISO),
                         SingleTimeEvent().next_trigger_time(now))

        self.timer.set_current_time(str_to_date("2018-01-01 13:44:50.000000", DateFormat.FULL_ISO))
        now = self.timer.now()

        self.assertEqual(str_to_date("2018-01-01 13:45:00.000000", DateFormat.FULL_ISO),
                         SingleTimeEvent().next_trigger_time(now))

        self.timer.set_current_time(SingleTimeEvent().next_trigger_time(now))
        now = self.timer.now()

        self.assertEqual(None, SingleTimeEvent().next_trigger_time(now))

    def test_simultaneous_time_event(self):

        def schedule_events():
            SingleTimeEvent.schedule_new_event(str_to_date("2017-04-10 14:00:00.000000", DateFormat.FULL_ISO), 1)
            SingleTimeEvent.schedule_new_event(str_to_date("2017-04-10 14:00:00.000000", DateFormat.FULL_ISO), 2)

        self.assertRaises(ValueError, schedule_events)


if __name__ == '__main__':
    unittest.main()
