import unittest
from unittest import TestCase

from qf_lib.backtesting.qstrader.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.common.utils.dateutils.string_to_date import str_to_date, DateFormat
from qf_lib.common.utils.dateutils.timer import SettableTimer


class TestRules(TestCase):

    def setUp(self):
        self.timer = SettableTimer()

    def test_market_open_rule(self):
        self.timer.set_current_time(str_to_date("2018-01-01 00:00:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = MarketOpenEvent.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-01 09:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        self.timer.set_current_time(str_to_date("2018-01-01 09:29:59.999999", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = MarketOpenEvent.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-01 09:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)

        self.timer.set_current_time(str_to_date("2018-01-01 09:30:00.000000", DateFormat.FULL_ISO))
        now = self.timer.now()
        next_trigger_time = MarketOpenEvent.next_trigger_time(now)
        self.assertEqual(str_to_date("2018-01-02 09:30:00.000000", DateFormat.FULL_ISO), next_trigger_time)


if __name__ == '__main__':
    unittest.main()
