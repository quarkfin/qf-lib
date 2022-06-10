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

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.tests.integration_tests.connect_to_data_provider import get_data_provider


class TestBloombergFutures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.start_date = str_to_date('2008-10-08')
        cls.end_date = str_to_date('2018-12-20')

        cls.timer = SettableTimer()
        cls.timer.set_current_time(cls.end_date)

        cls.frequency = Frequency.DAILY
        cls.ticker_1 = BloombergFutureTicker("Euroswiss", "ES{} Index", 1, 3, 100, "HMUZ")
        cls.ticker_2 = BloombergFutureTicker("Corn", "C {} Comdty", 1, 3, 100, "HKNUZ")

        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 00, "second": 0, "microsecond": 0})

    def setUp(self):
        try:
            self.data_provider = get_data_provider()
        except Exception as e:
            raise self.skipTest(e)

        self.ticker_1.initialize_data_provider(self.timer, self.data_provider)
        self.ticker_2.initialize_data_provider(self.timer, self.data_provider)

        self.timer.set_current_time(str_to_date("2017-12-20 00:00:00.000000", DateFormat.FULL_ISO))

    # =========================== Test get_futures and get_ticker with multiple PriceFields ============================

    def test_get_ticker_1st_contract_1_day_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-12-16"): BloombergTicker('ESZ16 Index'),
            str_to_date("2017-03-17"): BloombergTicker('ESH17 Index')
        }

        future_ticker = BloombergFutureTicker("Euroswiss", "ES{} Index", 1, 1, 100, "HMUZ")
        future_ticker.initialize_data_provider(self.timer, self.data_provider)

        # Check dates before 2016-12-16
        self.timer.set_current_time(str_to_date('2016-11-11'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-15'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-15 23:55:00.0', DateFormat.FULL_ISO))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        # On the expiry day, the next contract should be returned
        self.timer.set_current_time(str_to_date('2016-12-16'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2017-03-17")])

    def test_get_ticker_1st_contract_6_days_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-12-16"): BloombergTicker('ESZ16 Index'),
            str_to_date("2017-03-17"): BloombergTicker('ESH17 Index')
        }

        future_ticker = BloombergFutureTicker("Euroswiss", "ES{} Index", 1, 6, 100, "HMUZ")
        future_ticker.initialize_data_provider(self.timer, self.data_provider)

        # Check dates before 2016-12-16
        self.timer.set_current_time(str_to_date('2016-11-11'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-10'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-10 23:55:00.0', DateFormat.FULL_ISO))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-16'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2017-03-17")])

    def test_get_ticker_2nd_contract_1_day_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-06-30"): BloombergTicker('C N16 Comdty'),
            str_to_date("2016-08-31"): BloombergTicker('C U16 Comdty'),
            str_to_date("2016-11-30"): BloombergTicker('C Z16 Comdty')
        }

        future_ticker = BloombergFutureTicker("Corn", "C {} Comdty", 2, 1, 100, "HKNUZ")
        future_ticker.initialize_data_provider(self.timer, self.data_provider)

        self.timer.set_current_time(str_to_date('2016-06-03'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-08-31")])

        self.timer.set_current_time(str_to_date('2016-06-29'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-08-31")])

        self.timer.set_current_time(str_to_date('2016-06-29 23:59:59.0', DateFormat.FULL_ISO))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-08-31")])

        self.timer.set_current_time(str_to_date('2016-06-30'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-11-30")])

    def test_get_ticker_2nd_contract_6_days_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-06-30"): BloombergTicker('C N16 Comdty'),
            str_to_date("2016-08-31"): BloombergTicker('C U16 Comdty'),
            str_to_date("2016-11-30"): BloombergTicker('C Z16 Comdty')
        }

        future_ticker = BloombergFutureTicker("Corn", "C {} Comdty", 2, 6, 100, "HKNUZ")
        future_ticker.initialize_data_provider(self.timer, self.data_provider)

        self.timer.set_current_time(str_to_date('2016-06-03'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-08-31")])

        self.timer.set_current_time(str_to_date('2016-06-24 23:59:59.0', DateFormat.FULL_ISO))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-08-31")])

        self.timer.set_current_time(str_to_date('2016-07-09'))
        self.assertEqual(future_ticker.get_current_specific_ticker(),
                         exp_dates_to_ticker_str[str_to_date("2016-11-30")])

    # ========================================= Test get_expiration_dates ==============================================

    def test_get_expiration_dates(self):
        tickers_dict = self.data_provider.get_futures_chain_tickers(self.ticker_1, ExpirationDateField.all_dates())
        exp_dates = tickers_dict[self.ticker_1]

        self.assertEqual(type(exp_dates), QFDataFrame)

    # ========================================= Test BloombergFutureTicker =============================================

    def test_belongs_to_family(self):
        specific_tickers_different_family = [
            BloombergTicker("ES Z9 Index"),
            BloombergTicker("ESZ9 Comdty"),
            BloombergTicker("ESZ Index"),
            BloombergTicker("ESZ2019 Index"),
            BloombergTicker("ESZ9")
        ]

        for ticker in specific_tickers_different_family:
            self.assertFalse(self.ticker_1.belongs_to_family(ticker))

        self.assertTrue(self.ticker_1.belongs_to_family(BloombergTicker("ESZ9 Index", SecurityType.FUTURE, 100)))
