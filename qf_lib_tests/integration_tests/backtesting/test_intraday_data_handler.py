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

import os
import unittest
import pandas as pd
from unittest import TestCase

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.data_handler.intraday_data_handler import IntradayDataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.miscellaneous.get_cached_value import CachedValueException, cached_value
from qf_lib.containers.dimension_names import DATES
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_same_index
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not os.path.exists('Bloomberg_intraday_frequency_1_get_price.cache') and
                     not bbg_provider.connected, "No data available")
class TestIntradayDataHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spx_index_ticker = BloombergTicker("SPX Index")
        cls.google_ticker = BloombergTicker("GOOGL US Equity")
        cls.microsoft_ticker = BloombergTicker("MSFT US Equity")
        cls.price_field = [PriceField.Close]

        # Dates used for the intraday tests (the dates should not be older than 140 days)
        cls.fetch_data_start = str_to_date('2019-05-15 13:00:00.0', DateFormat.FULL_ISO)
        cls.fetch_data_end = str_to_date('2019-08-15 14:45:00.0', DateFormat.FULL_ISO)
        cls.start_date = str_to_date('2019-07-15 14:00:00.0', DateFormat.FULL_ISO)
        cls.end_date = str_to_date('2019-07-16 16:00:00.0', DateFormat.FULL_ISO)

        cls.frequency = Frequency.MIN_5

        cls.price_data_provider = cls.setUpDataProvider()

    @classmethod
    def setUpDataProvider(cls):
        # configure the data provider
        input_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(input_dir, 'Bloomberg_intraday_frequency_1_get_price.cache')

        def get_data_provider():
            if bbg_provider.connected:
                # Load the data with 1 minute frequency
                return bbg_provider.get_price([cls.spx_index_ticker, cls.google_ticker, cls.microsoft_ticker],
                                              PriceField.ohlcv(),
                                              cls.fetch_data_start,
                                              cls.fetch_data_end, Frequency.MIN_1)
            else:
                raise CachedValueException

        prefetched_data = cached_value(get_data_provider, filepath)

        return PresetDataProvider(prefetched_data, cls.fetch_data_start, cls.fetch_data_end, Frequency.MIN_1) if \
            prefetched_data is not None else None

    def setUp(self):
        self.timer = SettableTimer()
        self.data_handler = IntradayDataHandler(bbg_provider, self.timer)

        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    def test_get_price_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2019-07-17 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date, self.frequency)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date - self.frequency.time_delta(), prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(str_to_date("2019-07-16 22:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date, self.frequency)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(self.end_date - self.frequency.time_delta(), prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_tomorrow(self):
        current_time = str_to_date("2019-07-16 15:00:00.000000", DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date, self.frequency)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(current_time - self.frequency.time_delta(), prices_tms.index[-1].to_pydatetime())

    def test_get_price_when_end_date_is_before_end_of_current_hour_bar(self):
        current_time = str_to_date("2019-07-15 16:40:00.000000", DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date, Frequency.MIN_60)

        self.assertEqual(self.start_date, prices_tms.index[0].to_pydatetime())
        self.assertEqual(current_time - RelativeDelta(minutes=40), prices_tms.index[-1].to_pydatetime())

    def test_get_last_price_single_ticker(self):
        # during the trading session
        current_time = str_to_date("2019-07-15 15:00:00.000000", DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        current_price = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                    current_time - RelativeDelta(minutes=10),
                                                    current_time,
                                                    Frequency.MIN_1)
        current_price = current_price.values[-1]

        single_price = self.data_handler.get_last_available_price(self.spx_index_ticker, self.frequency)
        self.assertTrue(isinstance(single_price, float))
        self.assertEqual(current_price, single_price)

        during_the_day_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker], self.frequency)
        self.assertEqual(self.spx_index_ticker, during_the_day_last_prices.index[0])
        self.assertEqual(single_price, during_the_day_last_prices[0])

        # after the trading session
        self.timer.set_current_time(str_to_date("2019-07-15 22:00:00.000000", DateFormat.FULL_ISO))

        after_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker], self.frequency)

        self.assertEqual(self.spx_index_ticker, after_close_last_prices.index[0])
        self.assertNotEqual(during_the_day_last_prices[0], after_close_last_prices[0])

        # another time, after the trading session
        self.timer.set_current_time(str_to_date("2019-07-16 07:00:00.000000", DateFormat.FULL_ISO))

        after_close_last_prices2 = self.data_handler.get_last_available_price([self.spx_index_ticker], self.frequency)

        self.assertEqual(after_close_last_prices2[0], after_close_last_prices2[0])

        # before the trading session
        self.timer.set_current_time(str_to_date("2019-07-15 07:00:00.000000", DateFormat.FULL_ISO))
        before_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker], self.frequency)

        self.assertEqual(self.spx_index_ticker, before_close_last_prices.index[0])
        self.assertNotEqual(during_the_day_last_prices[0], before_close_last_prices[0])
        self.assertNotEqual(after_close_last_prices[0], before_close_last_prices[0])

    def test_get_last_price_with_multiple_tickers_when_current_data_is_unavailable(self):
        self.timer.set_current_time(str_to_date("2019-08-01 23:00:00.000000", DateFormat.FULL_ISO))
        last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker, self.google_ticker],
                                                                 self.frequency)

        self.assertEqual(self.spx_index_ticker, last_prices.index[0])
        self.assertEqual(self.google_ticker, last_prices.index[1])

    def test_get_last_price_before_first_bar_coming(self):
        self.timer.set_current_time(str_to_date("2019-07-18 23:36:00.000000", DateFormat.FULL_ISO))
        last_price = self.data_handler.get_last_available_price([self.microsoft_ticker], Frequency.MIN_15)

        self.timer.set_current_time(str_to_date("2019-07-19 07:44:55.000000", DateFormat.FULL_ISO))
        last_price2 = self.data_handler.get_last_available_price([self.microsoft_ticker], Frequency.MIN_15)

        self.assertEqual(last_price.values, last_price2.values)

    def test_historical_price_many_tickers_many_fields(self):
        self.timer.set_current_time(str_to_date("2019-07-31 15:00:00.000000", DateFormat.FULL_ISO))
        result_array = self.data_handler.historical_price([self.microsoft_ticker], [PriceField.Open, PriceField.Close],
                                                          nr_of_bars=5, frequency=self.frequency)

        self.assertEquals(QFDataArray, type(result_array))
        self.assertEquals((5, 1, 2), result_array.shape)

        expected_dates_str = ["2019-07-31 14:35:00.0",
                              "2019-07-31 14:40:00.0",
                              "2019-07-31 14:45:00.0",
                              "2019-07-31 14:50:00.0",
                              "2019-07-31 14:55:00.0"]
        expected_dates = [str_to_date(date_str, DateFormat.FULL_ISO) for date_str in expected_dates_str]
        assert_same_index(pd.DatetimeIndex(expected_dates, name=DATES), result_array.dates.to_index(),
                          check_index_type=True, check_names=True)

        self.timer.set_current_time(str_to_date("2019-07-31 15:04:00.000000", DateFormat.FULL_ISO))
        result_array = self.data_handler.historical_price([self.microsoft_ticker], [PriceField.Open, PriceField.Close],
                                                          nr_of_bars=3, frequency=self.frequency)

        expected_dates_str = ["2019-07-31 14:50:00.0",
                              "2019-07-31 14:55:00.0",
                              "2019-07-31 15:00:00.0"]
        expected_dates = [str_to_date(date_str, DateFormat.FULL_ISO) for date_str in expected_dates_str]
        assert_same_index(pd.DatetimeIndex(expected_dates, name=DATES), result_array.dates.to_index(),
                          check_index_type=True, check_names=True)

    def test_historical_price_many_tickers_many_fields_after_market_open(self):
        self.timer.set_current_time(str_to_date("2019-07-31 13:40:00.000000", DateFormat.FULL_ISO))
        result_array = self.data_handler.historical_price([self.microsoft_ticker], [PriceField.Open, PriceField.Close],
                                                          nr_of_bars=5, frequency=self.frequency)

        self.assertEquals(QFDataArray, type(result_array))
        self.assertEquals((5, 1, 2), result_array.shape)

        expected_dates_str = [
                              "2019-07-30 19:50:00.0",
                              "2019-07-30 19:55:00.0",
                              "2019-07-30 20:25:00.0",
                              "2019-07-31 13:30:00.0",
                              "2019-07-31 13:35:00.0"]
        expected_dates = [str_to_date(date_str, DateFormat.FULL_ISO) for date_str in expected_dates_str]
        assert_same_index(pd.DatetimeIndex(expected_dates, name=DATES), result_array.dates.to_index(),
                          check_index_type=True, check_names=True)

    def test_get_price_during_minute_bar(self):
        start_time = str_to_date("2019-07-15 17:39:00.000000", DateFormat.FULL_ISO)

        self.timer.set_current_time(str_to_date("2019-07-15 17:40:00.000000", DateFormat.FULL_ISO))
        data = self.data_handler.get_price(self.microsoft_ticker, PriceField.Close, start_time,
                                           frequency=Frequency.MIN_1)

        self.timer.set_current_time(str_to_date("2019-07-15 17:40:01.000000", DateFormat.FULL_ISO))
        data2 = self.data_handler.get_price(self.microsoft_ticker, PriceField.Close, start_time,
                                            frequency=Frequency.MIN_1)

        self.assertEqual(data.index[-1].to_pydatetime(), data2.index[-1].to_pydatetime())

    def test_current_and_last_price(self):
        # At the market open event the current price should point to the OPEN daily price
        current_time = str_to_date("2019-07-19 13:30:00.000000", DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time + MarketOpenEvent.trigger_time())

        last_price = self.data_handler.get_last_available_price([self.microsoft_ticker], Frequency.MIN_15)
        current_price = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.MIN_15)
        current_daily_price = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.DAILY)

        self.assertEqual(last_price.values, current_price.values)
        self.assertEqual(current_daily_price.values, current_price.values)

    def test_current_and_last_price_frequency_cast(self):
        # Current price for any intraday frequency should point to the same price
        self.timer.set_current_time(str_to_date("2019-07-19 14:30:00.000000", DateFormat.FULL_ISO))
        current_price = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.MIN_15)
        current_price_2 = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.MIN_10)
        current_price_3 = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.MIN_60)

        self.assertEqual(current_price.values, current_price_2.values)
        self.assertEqual(current_price.values, current_price_3.values)

    def test_current_and_last_price_seconds(self):
        # Current price in case of minutely frequency, outputs NaN in case of non zero seconds (or microseconds) part
        self.timer.set_current_time(str_to_date("2019-07-19 13:35:00.000000", DateFormat.FULL_ISO))

        last_price = self.data_handler.get_last_available_price([self.microsoft_ticker], Frequency.MIN_1)
        current_price = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.MIN_1)

        self.timer.set_current_time(str_to_date("2019-07-19 13:35:01.000000", DateFormat.FULL_ISO))

        last_price2 = self.data_handler.get_last_available_price([self.microsoft_ticker], Frequency.MIN_1)
        current_price2 = self.data_handler.get_current_price([self.microsoft_ticker], Frequency.MIN_1)

        self.assertEqual(last_price.values, current_price.values)
        self.assertEqual(last_price.values, last_price2.values)
        self.assertNotEqual(last_price2.values, current_price2.values)


if __name__ == '__main__':
    unittest.main()
