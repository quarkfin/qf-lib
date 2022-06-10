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
from unittest import TestCase

import pandas as pd

from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_same_index
from qf_lib.tests.integration_tests.connect_to_data_provider import get_data_provider


class TestDataHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spx_index_ticker = BloombergTicker("SPX Index")
        cls.google_ticker = BloombergTicker("GOOGL US Equity")
        cls.microsoft_ticker = BloombergTicker("MSFT US Equity")

        cls.start_date = str_to_date("2018-01-02")
        cls.end_date = str_to_date("2018-01-31")
        cls.end_date_trimmed = str_to_date("2018-01-30")
        cls.get_history_field = "PX_TO_BOOK_RATIO"

    def setUp(self):
        try:
            self.price_data_provider = get_data_provider()
        except Exception as e:
            raise self.skipTest(e)

        self.timer = SettableTimer()
        self.data_handler = DailyDataHandler(self.price_data_provider, self.timer)

        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    def test_get_price_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2018-02-12 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(
            str_to_date("2018-01-31") + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        close_prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close, self.start_date,
                                                       self.end_date)

        self.assertEqual(self.start_date, close_prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, close_prices_tms.index[-1].to_pydatetime())

    def test_get_open_price_when_end_date_is_today_before_market_close__single_ticker(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        open_prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Open, self.start_date)

        self.assertEqual(self.start_date, open_prices_tms.index[0].to_pydatetime())
        self.assertEqual(str_to_date("2018-01-30"), open_prices_tms.index[-1].to_pydatetime())

    def test_get_open_price_when_end_date_is_today_before_market_close__multiple_tickers(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        tickers = [self.spx_index_ticker, self.microsoft_ticker]
        open_prices_tms = self.data_handler.get_price(tickers, PriceField.Open, self.start_date, self.timer.now())

        self.assertEqual(self.start_date, open_prices_tms.index[0].to_pydatetime())
        self.assertEqual(str_to_date("2018-01-30"), open_prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(
            str_to_date("2018-01-30") + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close, self.start_date,
                                                 self.end_date_trimmed)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_last_price_single_ticker(self):
        with self.subTest("Test if getting single ticker value works, when a single ticker is passed"):
            self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() +
                                        RelativeDelta(hours=1))
            single_price = self.data_handler.get_last_available_price(self.spx_index_ticker)
            self.assertTrue(isinstance(single_price, float))

        with self.subTest("Test at market open"):
            self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time())
            at_market_open = self.data_handler.get_last_available_price([self.spx_index_ticker])

            self.assertEqual(self.spx_index_ticker, at_market_open.index[0])
            self.assertEqual(single_price, at_market_open[0])

        with self.subTest("Test during the trading session"):
            self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
            during_the_day_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

            self.assertEqual(self.spx_index_ticker, during_the_day_last_prices.index[0])
            self.assertEqual(single_price, during_the_day_last_prices[0])

        with self.subTest("Test after the trading session"):
            self.timer.set_current_time(
                str_to_date("2018-01-31") + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
            after_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

            self.assertEqual(self.spx_index_ticker, after_close_last_prices.index[0])
            self.assertNotEqual(during_the_day_last_prices[0], after_close_last_prices[0])

        with self.subTest("Test before the trading session"):
            self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() - RelativeDelta(hours=1))
            before_trading_session_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

            self.assertEqual(self.spx_index_ticker, before_trading_session_prices.index[0])
            self.assertNotEqual(during_the_day_last_prices[0], before_trading_session_prices[0])
            self.assertNotEqual(after_close_last_prices[0], before_trading_session_prices[0])

    def test_get_last_price_with_multiple_tickers_when_current_data_is_unavailable(self):
        self.timer.set_current_time(str_to_date("2018-01-01") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker, self.google_ticker])

        self.assertEqual(self.spx_index_ticker, last_prices.index[0])
        self.assertEqual(self.google_ticker, last_prices.index[1])

    def test_get_last_price_with_empty_tickers_list(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        last_prices = self.data_handler.get_last_available_price([])
        assert_series_equal(PricesSeries(), last_prices)

    def test_get_history_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2018-02-12 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, self.get_history_field,
                                                   self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(
            str_to_date("2018-01-31") + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, self.get_history_field,
                                                   self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, self.get_history_field,
                                                   self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(
            str_to_date("2018-01-30") + MarketCloseEvent.trigger_time() + RelativeDelta(hours=1))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, self.get_history_field,
                                                   self.start_date, self.end_date_trimmed)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_history_with_multiple_tickers(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        resilt_df = self.data_handler.get_history([self.microsoft_ticker, self.google_ticker], self.get_history_field,
                                                  self.start_date, self.end_date_trimmed)

        self.assertEqual(self.microsoft_ticker, resilt_df.columns[0])
        self.assertEqual(self.google_ticker, resilt_df.columns[1])
        self.assertEqual(self.start_date, resilt_df.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, resilt_df.index[-1].to_pydatetime())
        self.assertEqual(resilt_df.shape, (20, 2))

    def test_historical_price_many_tickers_many_fields(self):
        self.timer.set_current_time(str_to_date("2018-01-31") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        result_array = self.data_handler.historical_price([self.microsoft_ticker], [PriceField.Open, PriceField.Close],
                                                          nr_of_bars=5)

        self.assertEqual(QFDataArray, type(result_array))
        self.assertEqual((5, 1, 2), result_array.shape)

        expected_dates_str = ["2018-01-24", "2018-01-25", "2018-01-26", "2018-01-29", "2018-01-30"]
        expected_dates = [str_to_date(date_str) for date_str in expected_dates_str]
        assert_same_index(pd.DatetimeIndex(expected_dates, name=DATES), result_array.dates.to_index(),
                          check_index_type=True, check_names=True)

    def test_historical_price_many_tickers_one_field(self):
        self.timer.set_current_time(str_to_date("2018-01-04") + MarketOpenEvent.trigger_time() + RelativeDelta(hours=1))
        result_df = self.data_handler.historical_price([self.microsoft_ticker], PriceField.Open, nr_of_bars=5)

        self.assertEqual(PricesDataFrame, type(result_df))

        expected_dates_idx = pd.DatetimeIndex(
            ['2017-12-27', '2017-12-28', '2017-12-29', '2018-01-02', '2018-01-03'], name=DATES
        )
        assert_same_index(expected_dates_idx, result_df.index, check_index_type=True, check_names=True)

        expected_tickers_idx = pd.Index([self.microsoft_ticker], name=TICKERS)
        assert_same_index(expected_tickers_idx, result_df.columns, check_index_type=True, check_names=True)
