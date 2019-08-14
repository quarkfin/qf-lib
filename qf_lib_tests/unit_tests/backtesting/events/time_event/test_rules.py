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

from qf_lib.backtesting.events.time_event.market_open_event import MarketOpenEvent
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
