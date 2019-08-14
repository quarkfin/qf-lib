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

import pandas as pd

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_same_index
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestDataHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spx_index_ticker = BloombergTicker("SPX Index")
        cls.google_ticker = BloombergTicker("GOOGL US Equity")
        cls.microsoft_ticker = BloombergTicker("MSFT US Equity")

        cls.start_date = str_to_date("2018-01-02")
        cls.end_date = str_to_date("2018-01-31")
        cls.end_date_trimmed = str_to_date("2018-01-30")

    def setUp(self):
        self.price_data_provider = bbg_provider

        self.timer = SettableTimer()
        self.data_handler = DataHandler(self.price_data_provider, self.timer)

    def test_get_price_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2018-02-12 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 21:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(str_to_date("2018-01-30 18:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close, self.start_date,
                                                 self.end_date_trimmed)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_last_price_single_ticker(self):
        # just test if getting single ticker value works, when a single ticker (not wrapped in a list) is passed
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        single_price = self.data_handler.get_last_available_price(self.spx_index_ticker)
        self.assertTrue(isinstance(single_price, float))

        # during the trading session
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        during_the_day_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

        self.assertEqual(self.spx_index_ticker, during_the_day_last_prices.index[0])
        self.assertEqual(single_price, during_the_day_last_prices[0])

        # after the trading session
        self.timer.set_current_time(str_to_date("2018-01-31 20:00:00.000000", DateFormat.FULL_ISO))
        after_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

        self.assertEqual(self.spx_index_ticker, after_close_last_prices.index[0])
        self.assertNotEqual(during_the_day_last_prices[0], after_close_last_prices[0])

        # before the trading session
        self.timer.set_current_time(str_to_date("2018-01-31 07:00:00.000000", DateFormat.FULL_ISO))
        before_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

        self.assertEqual(self.spx_index_ticker, before_close_last_prices.index[0])
        self.assertNotEqual(during_the_day_last_prices[0], before_close_last_prices[0])
        self.assertNotEqual(after_close_last_prices[0], before_close_last_prices[0])

    def test_get_last_price_with_multiple_tickers_when_current_data_is_unavailable(self):
        self.timer.set_current_time(str_to_date("2018-01-01 12:00:00.000000", DateFormat.FULL_ISO))
        last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker, self.google_ticker])

        self.assertEqual(self.spx_index_ticker, last_prices.index[0])
        self.assertEqual(self.google_ticker, last_prices.index[1])

    def test_get_last_price_with_empty_tickers_list(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        last_prices = self.data_handler.get_last_available_price([])
        assert_series_equal(pd.Series(), last_prices)

    def test_get_history_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2018-02-12 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 21:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date, prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_history_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(str_to_date("2018-01-30 18:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date_trimmed)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, prices_tms.index[-1].to_pydatetime())

    def test_get_history_with_multiple_tickers(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        resilt_df = self.data_handler.get_history([self.microsoft_ticker, self.google_ticker], 'PX_TO_BOOK_RATIO',
                                                  self.start_date, self.end_date_trimmed)

        self.assertEqual(self.microsoft_ticker, resilt_df.columns[0])
        self.assertEqual(self.google_ticker, resilt_df.columns[1])
        self.assertEqual(self.start_date, resilt_df.index[0].to_pydatetime())
        self.assertEqual(self.end_date_trimmed, resilt_df.index[-1].to_pydatetime())
        self.assertEqual(resilt_df.shape, (20, 2))

    def test_historical_price_many_tickers_many_fields(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        result_array = self.data_handler.historical_price([self.microsoft_ticker], [PriceField.Open, PriceField.Close],
                                                          nr_of_bars=5)

        self.assertEquals(QFDataArray, type(result_array))
        self.assertEquals((5, 1, 2), result_array.shape)

        expected_dates_str = ["2018-01-24", "2018-01-25", "2018-01-26", "2018-01-29", "2018-01-30"]
        expected_dates = [str_to_date(date_str) for date_str in expected_dates_str]
        assert_same_index(pd.DatetimeIndex(expected_dates, name=DATES), result_array.dates.to_index(),
                          check_index_type=True, check_names=True)

    def test_historical_price_many_tickers_one_field(self):
        self.timer.set_current_time(str_to_date("2018-01-04 12:00:00.000000", DateFormat.FULL_ISO))
        result_df = self.data_handler.historical_price([self.microsoft_ticker], PriceField.Open, nr_of_bars=5)

        self.assertEquals(PricesDataFrame, type(result_df))

        expected_dates_idx = pd.DatetimeIndex(
            ['2017-12-27', '2017-12-28', '2017-12-29', '2018-01-02', '2018-01-03'], name=DATES
        )
        assert_same_index(expected_dates_idx, result_df.index, check_index_type=True, check_names=True)

        expected_tickers_idx = pd.Index([self.microsoft_ticker], name=TICKERS)
        assert_same_index(expected_tickers_idx, result_df.columns, check_index_type=True, check_names=True)


if __name__ == '__main__':
    unittest.main()
