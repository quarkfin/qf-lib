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

from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_ticker import BloombergFutureTicker
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestBloombergFutures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.timer = SettableTimer()
        cls.frequency = Frequency.DAILY
        cls.ticker_1 = BloombergFutureTicker("ES", "ES{} Index", cls.timer, bbg_provider, 1, 3, 100, "HMUZ")
        cls.ticker_2 = BloombergFutureTicker("Corn", "C {} Comdty", cls.timer, bbg_provider, 1, 3, 100, "HKNUZ")

        cls.start_date = str_to_date('2008-10-08')
        cls.end_date = str_to_date('2018-12-20')

        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 00, "second": 0, "microsecond": 0})

    def setUp(self):
        self.data_handler = DailyDataHandler(bbg_provider, self.timer)

        self.timer.set_current_time(str_to_date("2017-12-20 00:00:00.000000", DateFormat.FULL_ISO))

    # =========================== Test get_futures and get_ticker with multiple PriceFields ============================

    def test_get_ticker_1st_contract_1_day_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-12-16"): BloombergTicker('ESZ16 Index'),
            str_to_date("2017-03-17"): BloombergTicker('ESH17 Index')
        }

        future_ticker = BloombergFutureTicker("ES", "ES{} Index", self.timer, bbg_provider, 1, 1, 100, "HMUZ")
        futures_chains_dict = self.data_handler.get_futures(future_ticker,
                                                            PriceField.ohlcv(),
                                                            self.start_date, self.end_date)
        futures_chain = futures_chains_dict[future_ticker]
        self.assertEqual(FuturesChain, type(futures_chain))

        # Check dates before 2016-12-16
        self.timer.set_current_time(str_to_date('2016-11-11'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-15'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-15 23:55:00.0', DateFormat.FULL_ISO))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        # On the expiry day, the next contract should be returned
        self.timer.set_current_time(str_to_date('2016-12-16'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2017-03-17")])

    def test_get_ticker_1st_contract_6_days_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-12-16"): BloombergTicker('ESZ16 Index'),
            str_to_date("2017-03-17"): BloombergTicker('ESH17 Index')
        }

        future_ticker = BloombergFutureTicker("ES", "ES{} Index", self.timer, bbg_provider, 1, 6, 100, "HMUZ")
        futures_chains_dict = self.data_handler.get_futures(future_ticker,
                                                            PriceField.ohlcv(),
                                                            self.start_date, self.end_date)
        futures_chain = futures_chains_dict[future_ticker]
        self.assertEqual(FuturesChain, type(futures_chain))

        # Check dates before 2016-12-16
        self.timer.set_current_time(str_to_date('2016-11-11'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-10'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-10 23:55:00.0', DateFormat.FULL_ISO))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.timer.set_current_time(str_to_date('2016-12-16'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2017-03-17")])

    def test_get_ticker_2nd_contract_1_day_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-07-01"): BloombergTicker('C N16 Comdty'),
            str_to_date("2016-09-01"): BloombergTicker('C U16 Comdty'),
            str_to_date("2016-12-01"): BloombergTicker('C Z16 Comdty')
        }

        future_ticker = BloombergFutureTicker("Corn", "C {} Comdty", self.timer, bbg_provider, 2, 1, 100, "HKNUZ")
        futures_chains_dict = self.data_handler.get_futures(future_ticker,
                                                            PriceField.ohlcv(),
                                                            self.start_date, self.end_date)
        futures_chain = futures_chains_dict[future_ticker]

        self.timer.set_current_time(str_to_date('2016-06-03'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-09-01")])

        self.timer.set_current_time(str_to_date('2016-06-30'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-09-01")])

        self.timer.set_current_time(str_to_date('2016-06-30 23:59:59.0', DateFormat.FULL_ISO))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-09-01")])

        self.timer.set_current_time(str_to_date('2016-07-01'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-01")])

    def test_get_ticker_2nd_contract_6_days_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-07-01"): BloombergTicker('C N16 Comdty'),
            str_to_date("2016-09-01"): BloombergTicker('C U16 Comdty'),
            str_to_date("2016-12-01"): BloombergTicker('C Z16 Comdty')
        }

        future_ticker = BloombergFutureTicker("Corn", "C {} Comdty", self.timer, bbg_provider, 2, 6, 100, "HKNUZ")
        futures_chains_dict = self.data_handler.get_futures(future_ticker,
                                                            PriceField.ohlcv(),
                                                            self.start_date, self.end_date)
        futures_chain = futures_chains_dict[future_ticker]

        self.timer.set_current_time(str_to_date('2016-06-03'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-09-01")])

        self.timer.set_current_time(str_to_date('2016-06-25 23:59:59.0', DateFormat.FULL_ISO))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-09-01")])

        self.timer.set_current_time(str_to_date('2016-06-26'))
        self.assertEqual(futures_chain.get_ticker(), exp_dates_to_ticker_str[str_to_date("2016-12-01")])

    # ============================== Test get_futures with one PriceField ===============================

    def test_get_futures_1_price_field(self):
        futures_chains_dict = self.data_handler.get_futures([self.ticker_1, self.ticker_2],
                                                            PriceField.Close,
                                                            self.start_date, self.end_date)
        futures_chain = futures_chains_dict[self.ticker_1]
        self.assertEqual(FuturesChain, type(futures_chain))

    def test_get_futures_multiple_price_fields(self):
        futures_chains_dict = self.data_handler.get_futures([self.ticker_1, self.ticker_2],
                                                            PriceField.ohlcv(),
                                                            self.start_date, self.end_date)
        futures_chain = futures_chains_dict[self.ticker_1]
        self.assertEqual(FuturesChain, type(futures_chain))

    # ========================================= Test get_expiration_dates ==============================================

    def test_get_expiration_dates(self):
        date = str_to_date("2016-07-14")
        tickers_dict = bbg_provider.get_futures_chain_tickers(self.ticker_1, date)
        exp_dates = tickers_dict[self.ticker_1]

        self.assertEqual(type(exp_dates), QFSeries)

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

        self.assertTrue(self.ticker_1.belongs_to_family(BloombergTicker("ESZ9 Index")))
