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

from qf_lib.backtesting.data_handler.data_handler import _DataHandlerTimeHelper
from qf_lib.backtesting.events.time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer


class TestDataHandlerTimeHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.YESTERDAY_OPEN = str_to_date("2018-01-29 09:30:00.000000", DateFormat.FULL_ISO)
        cls.YESTERDAY_CLOSE = str_to_date("2018-01-29 16:00:00.000000", DateFormat.FULL_ISO)
        cls.TODAY_BEFORE_OPEN = str_to_date("2018-01-30 06:00:00.000000", DateFormat.FULL_ISO)
        cls.TODAY_OPEN = str_to_date("2018-01-30 09:30:00.000000", DateFormat.FULL_ISO)
        cls.TODAY_MIDDLE_DAY = str_to_date("2018-01-30 12:00:00.000000", DateFormat.FULL_ISO)
        cls.TODAY_CLOSE = str_to_date("2018-01-30 16:00:00.000000", DateFormat.FULL_ISO)
        cls.TODAY_AFTER_CLOSE = str_to_date("2018-01-30 20:00:00.000000", DateFormat.FULL_ISO)

    def setUp(self):
        self.timer = SettableTimer()
        self.time_helper = _DataHandlerTimeHelper(self.timer)

    def test_datetime_of_latest_market_event_before_market_open(self):
        self.timer.set_current_time(self.TODAY_BEFORE_OPEN)

        market_open_datetime = self.time_helper.datetime_of_latest_market_event(MarketOpenEvent)
        market_close_datetime = self.time_helper.datetime_of_latest_market_event(MarketCloseEvent)

        self.assertEqual(market_open_datetime, self.YESTERDAY_OPEN)
        self.assertEqual(market_close_datetime, self.YESTERDAY_CLOSE)

    def test_datetime_of_latest_market_event_during_trading_session(self):
        self.timer.set_current_time(self.TODAY_MIDDLE_DAY)

        market_open_datetime = self.time_helper.datetime_of_latest_market_event(MarketOpenEvent)
        market_close_datetime = self.time_helper.datetime_of_latest_market_event(MarketCloseEvent)

        self.assertEqual(market_open_datetime, self.TODAY_OPEN)
        self.assertEqual(market_close_datetime, self.YESTERDAY_CLOSE)

    def test_datetime_of_latest_market_event_after_market_close(self):
        self.timer.set_current_time(self.TODAY_AFTER_CLOSE)

        market_open_datetime = self.time_helper.datetime_of_latest_market_event(MarketOpenEvent)
        market_close_datetime = self.time_helper.datetime_of_latest_market_event(MarketCloseEvent)

        self.assertEqual(market_open_datetime, self.TODAY_OPEN)
        self.assertEqual(market_close_datetime, self.TODAY_CLOSE)


if __name__ == '__main__':
    unittest.main()
