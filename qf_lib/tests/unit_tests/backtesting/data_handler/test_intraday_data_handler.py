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
from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock

from numpy import nan, concatenate
from pandas import date_range, isnull, concat, Index, DatetimeIndex

from qf_lib.backtesting.data_handler.intraday_data_handler import IntradayDataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker, Ticker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import TICKERS, DATES, FIELDS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal, \
    assert_dataarrays_equal


class TestIntradayDataHandler(TestCase):
    def setUp(self):
        self.timer = SettableTimer()
        self.tickers = [QuandlTicker("MSFT", "WIKI"), QuandlTicker("AAPL", "WIKI")]
        price_data_provider_mock_MIN_1 = self._create_price_provider_mock(self.tickers, frequency=Frequency.MIN_1)
        price_data_provider_mock_MIN_5 = self._create_price_provider_mock(self.tickers, frequency=Frequency.MIN_5)
        price_data_provider_mock_MIN_60 = self._create_price_provider_mock(self.tickers, frequency=Frequency.MIN_60)

        self.data_handler_MIN_1 = IntradayDataHandler(price_data_provider_mock_MIN_1, self.timer)
        self.data_handler_MIN_5 = IntradayDataHandler(price_data_provider_mock_MIN_5, self.timer)
        self.data_handler_MIN_60 = IntradayDataHandler(price_data_provider_mock_MIN_60, self.timer)

        self.data_handlers = {Frequency.MIN_1: self.data_handler_MIN_1,
                              Frequency.MIN_5: self.data_handler_MIN_5,
                              Frequency.MIN_60: self.data_handler_MIN_60}

        MarketOpenEvent.set_trigger_time({"hour": 8, "minute": 0, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 16, "minute": 0, "second": 0, "microsecond": 0})

    def test_last_available_price_before_data_starts(self):
        self._assert_last_prices_are_correct("2009-12-30 06:00:00.000000", [nan, nan], Frequency.MIN_1)

    def test_last_available_price_at_market_open_when_data_available_for_the_first_ticker(self):
        self._assert_last_prices_are_correct("2009-12-30 8:00:00.000000", [43.4, 33.2], Frequency.MIN_1)

    def test_last_available_price_during_trading_hours_when_data_available_for_the_first_ticker(self):
        self._assert_last_prices_are_correct("2009-12-30 15:57:00.000000", [45.1, 36.0], Frequency.MIN_1)

    def test_last_available_price_at_market_close_when_data_available_for_the_second_ticker(self):
        self._assert_last_prices_are_correct("2009-12-30 16:00:00.000000", [45.6, 29.8], Frequency.MIN_1)

    def test_last_available_price_after_market_close_when_data_is_not_available_for_anything_anymore(self):
        self._assert_last_prices_are_correct("2009-12-30 20:00:00.000000", [45.5, 30.7], Frequency.MIN_1)

    def test_last_available_price_before_market_open_when_old_data_is_available(self):
        self._assert_last_prices_are_correct("2009-12-31 06:00:00.000000", [45.5, 30.7], Frequency.MIN_1)

    def test_last_available_price_during_trading_bar_hours_when_data_available_for_the_first_ticker(self):
        self._assert_last_prices_are_correct("2009-12-30 15:57:01.000000", [45.1, 36.0], Frequency.MIN_1)

    def test_last_available_price_during_trading_hours_when_data_available_for_the_first_ticker_freq5(self):
        self._assert_last_prices_are_correct("2009-12-30 15:45:00.000000", [45.1, 36.0], Frequency.MIN_5)

    def test_last_available_price_during_trading_bar_hours_when_data_available_for_the_first_ticker_freq5(self):
        self._assert_last_prices_are_correct("2009-12-30 15:45:00.100000", [45.1, 36.0], Frequency.MIN_5)

    def test_last_available_price_during_trading_bar_hours_when_data_available_for_the_second_ticker_freq5(self):
        self._assert_last_prices_are_correct("2009-12-30 15:44:59.000000", [52.2, 36.0], Frequency.MIN_5)

    def test_last_available_price_during_trading_hours_when_data_available_for_the_first_ticker_freq60(self):
        self._assert_last_prices_are_correct("2009-12-30 13:00:00.000000", [45.1, 36.0], Frequency.MIN_60)

    def test_last_available_price_during_trading_bar_hours_when_data_available_for_the_first_ticker_freq60(self):
        self._assert_last_prices_are_correct("2009-12-30 13:00:00.100000", [45.1, 36.0], Frequency.MIN_60)

    def test_last_available_price_during_trading_bar_hours_when_data_available_for_the_second_ticker_freq60(self):
        self._assert_last_prices_are_correct("2009-12-30 12:44:59.000000", [52.2, 36.0], Frequency.MIN_60)

    def test_last_available_price_with_end_date(self):
        self._assert_last_prices_are_correct_with_end_date("2009-12-30 20:00:00.100000",
                                                           "2009-12-30 13:00:00.100000", [45.1, 36.0], Frequency.MIN_60)

    def test_get_price_before_market_close_single_date_single_field_single_ticker_empty_container(self):
        start_date = datetime(2009, 12, 30, 15, 56)
        end_date = datetime(2009, 12, 30, 15, 56)

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-30 15:56:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_single_date_single_field_single_ticker_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 4)
        end_date = datetime(2009, 12, 30, 16, 4)

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-30 16:04:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - single date, single field, single ticker """

    def test_get_price_before_market_open_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 7, 58)
        end_date = datetime(2009, 12, 30, 7, 58)

        expected_result = 32.2
        self._assert_get_prices_are_correct("2009-12-30 7:59:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_at_market_open_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 8)
        end_date = datetime(2009, 12, 30, 8)

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-30 8:00:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-30 8:00:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_during_trading_hours_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 8, 1)
        end_date = datetime(2009, 12, 30, 8, 1)

        expected_result = 48.5
        self._assert_get_prices_are_correct("2009-12-30 8:03:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = 49.0
        self._assert_get_prices_are_correct("2009-12-30 8:03:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_at_market_close_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 15, 59)
        end_date = datetime(2009, 12, 30, 15, 59)

        expected_result = 29.3
        self._assert_get_prices_are_correct("2009-12-30 16:00:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = 29.7
        self._assert_get_prices_are_correct("2009-12-30 16:00:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 2)

        expected_result = 45.7
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = 45.65
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 2)

        expected_result = 45.7
        self._assert_get_prices_are_correct("2009-12-30 16:03:01.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = 45.65
        self._assert_get_prices_are_correct("2009-12-30 16:03:01.100000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-30 16:02:59.100000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_single_date_single_field_single_ticker_freq5(self):
        start_date = datetime(2009, 12, 30, 16, 10)
        end_date = datetime(2009, 12, 30, 16, 10)

        expected_result = 45.7
        self._assert_get_prices_are_correct("2009-12-30 16:15:01.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_5)

        expected_result = 45.65
        self._assert_get_prices_are_correct("2009-12-30 16:15:00.100000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_5)

    def test_get_price_after_market_close_during_bar_single_date_single_field_single_ticker_freq60(self):
        start_date = datetime(2009, 12, 30, 17)
        end_date = datetime(2009, 12, 30, 17)

        expected_result = 45.6
        self._assert_get_prices_are_correct("2009-12-30 18:45:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_60)

        start_date = datetime(2009, 12, 30, 16)
        end_date = datetime(2009, 12, 30, 16)
        expected_result = 30.1
        self._assert_get_prices_are_correct("2009-12-30 17:59:0.100000", start_date, end_date, self.tickers[1],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_60)

    def test_get_price_before_next_open_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 16, 3)
        end_date = datetime(2009, 12, 30, 16, 3)

        expected_result = 45.8
        self._assert_get_prices_are_correct("2009-12-31 7:59:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = 45.5
        self._assert_get_prices_are_correct("2009-12-31 7:59:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - single date, single field, multiple tickers """

    def test_get_price_before_market_close_single_date_single_field_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 15, 56)
        end_date = datetime(2009, 12, 30, 15, 56)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-30 15:58:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_single_date_single_field_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 2)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open, data=[45.7, nan])
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Close, data=[45.65, nan])
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_before_market_close_single_date_single_field_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 15, 56)
        end_date = datetime(2009, 12, 30, 15, 56)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-30 15:56:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_before_market_close_during_bar_single_date_single_field_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 15, 56)
        end_date = datetime(2009, 12, 30, 15, 56)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-30 15:56:00.100000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_before_market_close_during_bar_single_date_single_field_multiple_tickers_empty_container_freq5(self):
        start_date = datetime(2009, 12, 30, 15, 56)
        end_date = datetime(2009, 12, 30, 15, 56)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-30 15:57:00.100000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_5)

    def test_get_price_before_market_close_during_bar_single_date_single_field_multiple_tickers_empty_container_freq60(self):
        start_date = datetime(2009, 12, 30, 15, 56)
        end_date = datetime(2009, 12, 30, 15, 56)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-30 15:59:00.100000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_60)

    def test_get_price_after_market_close_single_date_single_field_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 4)
        end_date = datetime(2009, 12, 30, 16, 4)

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-30 16:04:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - single date, multiple fields, single ticker """

    def test_get_price_before_market_close_single_date_multiple_fields_single_ticker(self):
        start_date = datetime(2009, 12, 30, 15, 57)
        end_date = datetime(2009, 12, 30, 15, 57)

        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       name=self.tickers[0].as_string(), data=[45.1, 45.3])
        self._assert_get_prices_are_correct("2009-12-30 15:58:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_single_date_multiple_fields_single_ticker(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 2)

        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       name=self.tickers[0].as_string(), data=[45.7, 45.65])
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_single_date_multiple_fields_single_ticker_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 4)
        end_date = datetime(2009, 12, 30, 16, 4)

        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       name=self.tickers[0].as_string())
        self._assert_get_prices_are_correct("2009-12-30 16:04:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - single date, multiple fields, multiple tickers """

    def test_get_price_before_market_close_single_date_multiple_fields_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 15, 57)
        end_date = datetime(2009, 12, 30, 15, 57)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=[[45.1, 45.3], [nan, nan]])
        self._assert_get_prices_are_correct("2009-12-30 15:58:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_before_market_close_single_date_multiple_fields_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 4)
        end_date = datetime(2009, 12, 30, 16, 4)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=None)
        self._assert_get_prices_are_correct("2009-12-30 16:04:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_single_date_multiple_fields_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 2)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=[[45.7, 45.65], [nan, nan]])
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_single_date_multiple_fields_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 2)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=[[45.7, 45.65], [nan, nan]])
        self._assert_get_prices_are_correct("2009-12-30 16:03:00.100000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_single_date_multiple_fields_multiple_tickers_freq5(self):
        start_date = datetime(2009, 12, 30, 16, 10)
        end_date = datetime(2009, 12, 30, 16, 10)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=[[45.7, 45.65], [nan, nan]])
        self._assert_get_prices_are_correct("2009-12-30 16:15:00.100000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_5)

    def test_get_price_after_market_close_during_bar_single_date_multiple_fields_multiple_tickers_freq60(self):
        start_date = datetime(2009, 12, 30, 17)
        end_date = datetime(2009, 12, 30, 17)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=[[45.6, 46.2], [30.1, 30.3]])
        self._assert_get_prices_are_correct("2009-12-30 18:00:00.100000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_60)

    def test_get_price_after_market_close_single_date_multiple_fields_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 4)
        end_date = datetime(2009, 12, 30, 16, 4)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=None)
        self._assert_get_prices_are_correct("2009-12-30 16:04:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - multiple dates, single field, single ticker """

    def test_get_price_before_data_multiple_dates_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 15, 55)
        end_date = datetime(2009, 12, 30, 16, 0)

        fields = PriceField.Open
        expected_result = PricesSeries(name=self.tickers[0].as_string(),
                                       index=DatetimeIndex([datetime(2009, 12, 30, 15, 57),
                                                            datetime(2009, 12, 30, 15, 58)], name=DATES),
                                       data=[45.1, 45.3])
        self._assert_get_prices_are_correct("2009-12-30 15:59:00.000000", start_date, end_date, self.tickers[0],
                                            fields, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_multiple_dates_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 5)

        fields = PriceField.Open
        expected_result = PricesSeries(name=self.tickers[0].as_string(),
                                       index=DatetimeIndex([datetime(2009, 12, 30, 16, 2),
                                                            datetime(2009, 12, 30, 16, 3)],
                                                           name=DATES),
                                       data=[45.7, 45.8])
        self._assert_get_prices_are_correct("2009-12-30 16:05:00.000000", start_date, end_date, self.tickers[0],
                                            fields, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_multiple_dates_single_field_single_ticker_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 5)
        end_date = datetime(2009, 12, 30, 16, 10)

        fields = PriceField.Open
        expected_result = PricesSeries(name=self.tickers[0].as_string(), index=DatetimeIndex([], name=DATES))
        self._assert_get_prices_are_correct("2009-12-30 16:15:00.000000", start_date, end_date, self.tickers[0],
                                            fields, expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - multiple dates, single field, multiple tickers """

    def test_get_price_before_data_multiple_dates_single_field_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 15, 55)
        end_date = datetime(2009, 12, 30, 16, 0)

        fields = PriceField.Open
        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 15, 57),
                                                               datetime(2009, 12, 30, 15, 58)],
                                                              name=DATES),
                                          data=[[45.1, nan], [45.3, 29.1]])
        expected_result.name = fields
        self._assert_get_prices_are_correct("2009-12-30 15:59:00.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_multiple_dates_single_field_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 5)

        fields = PriceField.Open
        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 16, 2),
                                                               datetime(2009, 12, 30, 16, 3)],
                                                              name=DATES),
                                          data=[[45.7, nan], [45.8, 30.4]])
        expected_result.name = fields
        self._assert_get_prices_are_correct("2009-12-30 16:05:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_multiple_dates_single_field_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 1)
        end_date = datetime(2009, 12, 30, 16, 5)

        fields = PriceField.Open
        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 16, 1)], name=DATES),
                                          data=[[45.6, 30.1]])
        expected_result.name = fields
        self._assert_get_prices_are_correct("2009-12-30 16:02:59.999999", start_date, end_date, self.tickers,
                                            fields, expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_multiple_dates_single_field_multiple_tickers_freq5(self):
        start_date = datetime(2009, 12, 30, 16, 0)
        end_date = datetime(2009, 12, 30, 16, 20)

        fields = PriceField.Open
        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 16, 0)], name=DATES),
                                          data=[[nan, 29.8]])
        expected_result.name = fields
        self._assert_get_prices_are_correct("2009-12-30 16:05:59.999999", start_date, end_date, self.tickers,
                                            fields, expected_result, frequency=Frequency.MIN_5)

    def test_get_price_after_market_close_during_bar_multiple_dates_single_field_multiple_tickers_freq60(self):
        start_date = datetime(2009, 12, 30, 15)
        end_date = datetime(2009, 12, 30, 20)

        fields = PriceField.Open
        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 15)], name=DATES),
                                          data=[[nan, 29.3]])
        expected_result.name = fields
        self._assert_get_prices_are_correct("2009-12-30 16:02:59.999999", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_60)

    def test_get_price_after_market_close_multiple_dates_single_field_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 5)
        end_date = datetime(2009, 12, 30, 16, 10)

        fields = PriceField.Open
        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS), index=DatetimeIndex([], name=DATES))
        expected_result.name = fields
        self._assert_get_prices_are_correct("2009-12-30 16:15:00.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - multiple dates, multiple fields, single ticker """

    def test_get_price_before_data_multiple_dates_multiple_fields_single_ticker(self):
        start_date = datetime(2009, 12, 30, 15, 55)
        end_date = datetime(2009, 12, 30, 16, 0)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 15, 57),
                                                               datetime(2009, 12, 30, 15, 58)],
                                                              name=DATES),
                                          data=[45.1, 45.3])
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 15:59:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_before_data_during_bar_multiple_dates_multiple_fields_single_ticker(self):
        start_date = datetime(2009, 12, 30, 15, 55)
        end_date = datetime(2009, 12, 30, 16, 0)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 15, 57)], name=DATES), data=[45.1])
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 15:58:59.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_before_data_during_bar_multiple_dates_multiple_fields_single_ticker_freq5(self):
        start_date = datetime(2009, 12, 30, 15, 30)
        end_date = datetime(2009, 12, 30, 16, 0)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 15, 45)], name=DATES), data=[45.1])
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 15:51:59.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result, frequency=Frequency.MIN_5)

    def test_get_price_before_data_during_bar_multiple_dates_multiple_fields_single_ticker_freq60(self):
        start_date = datetime(2009, 12, 30, 12)
        end_date = datetime(2009, 12, 30, 16)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 13)], name=DATES), data=[45.1])
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 14:00:00.100000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result, frequency=Frequency.MIN_60)

    def test_get_price_after_market_close_multiple_dates_multiple_fields_single_ticker(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 5)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([datetime(2009, 12, 30, 16, 2),
                                                               datetime(2009, 12, 30, 16, 3)],
                                                              name=DATES),
                                          data=[45.7, 45.8])

        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 16:05:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_multiple_dates_multiple_fields_single_ticker_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 5)
        end_date = datetime(2009, 12, 30, 16, 10)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([], name=DATES))
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 16:15:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result, frequency=Frequency.MIN_1)

    """ Test get_price function - multiple dates, multiple fields, multiple tickers """

    def test_get_price_before_data_multiple_dates_multiple_fields_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 15, 55)
        end_date = datetime(2009, 12, 30, 16, 0)

        fields = [PriceField.Open]
        expected_result = QFDataArray.create([datetime(2009, 12, 30, 15, 57), datetime(2009, 12, 30, 15, 58)],
                                             self.tickers, fields, data=[[[45.1], [nan]], [[45.3], [29.1]]])
        self._assert_get_prices_are_correct("2009-12-30 15:59:00.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_multiple_dates_multiple_fields_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 2)
        end_date = datetime(2009, 12, 30, 16, 5)

        fields = [PriceField.Open]
        expected_result = QFDataArray.create([datetime(2009, 12, 30, 16, 2), datetime(2009, 12, 30, 16, 3)],
                                             self.tickers, fields, data=[[[45.7], [nan]], [[45.8], [30.4]]])
        self._assert_get_prices_are_correct("2009-12-30 16:05:00.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_multiple_dates_multiple_fields_multiple_tickers(self):
        start_date = datetime(2009, 12, 30, 16, 1)
        end_date = datetime(2009, 12, 30, 16, 5)

        fields = [PriceField.Open]
        expected_result = QFDataArray.create([datetime(2009, 12, 30, 16, 1)], self.tickers, fields,
                                             data=[[[45.6], [30.1]]])
        self._assert_get_prices_are_correct("2009-12-30 16:02:59.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_1)

    def test_get_price_after_market_close_during_bar_multiple_dates_multiple_fields_multiple_tickers_freq5(self):
        start_date = datetime(2009, 12, 30, 16, 10)
        end_date = datetime(2009, 12, 30, 20)

        fields = [PriceField.Open]
        expected_result = QFDataArray.create([datetime(2009, 12, 30, 16, 10)], self.tickers, fields,
                                             data=[[[45.7], [nan]]])
        self._assert_get_prices_are_correct("2009-12-30 16:15:01.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_5)

    def test_get_price_after_market_close_during_bar_multiple_dates_multiple_fields_multiple_tickers_freq60(self):
        start_date = datetime(2009, 12, 30, 16, 5)
        end_date = datetime(2009, 12, 30, 20)

        fields = [PriceField.Open]
        expected_result = QFDataArray.create([datetime(2009, 12, 30, 16, 5)], self.tickers, fields,
                                             data=[[[45.6], [30.1]]])
        self._assert_get_prices_are_correct("2009-12-30 16:10:12.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_5)

    def test_get_price_after_market_close_multiple_dates_multiple_fields_multiple_tickers_empty_container(self):
        start_date = datetime(2009, 12, 30, 16, 5)
        end_date = datetime(2009, 12, 30, 16, 10)
        fields = [PriceField.Open]

        expected_result = QFDataArray.create(DatetimeIndex([], name=DATES), self.tickers, fields, data=None)
        expected_result = normalize_data_array(expected_result, self.tickers, fields, False, False, False)
        self._assert_get_prices_are_correct("2009-12-30 16:15:00.000000", start_date, end_date, self.tickers, fields,
                                            expected_result, frequency=Frequency.MIN_1)

    def test_get_price_during_trading_bar_hours_single_date_single_field_single_ticker(self):
        start_date = datetime(2009, 12, 30, 8, 1)
        end_date = datetime(2009, 12, 30, 8, 1)

        expected_result = 48.5
        self._assert_get_prices_are_correct("2009-12-30 8:03:01.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result, frequency=Frequency.MIN_1)

        expected_result = 49.0
        self._assert_get_prices_are_correct("2009-12-30 8:03:01.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Close, expected_result, frequency=Frequency.MIN_1)

    def _assert_last_prices_are_correct(self, curr_time_str, expected_values, frequency):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        expected_series = PricesSeries(data=expected_values, index=self.tickers)
        actual_series = self.data_handlers[frequency].get_last_available_price(self.tickers)
        assert_series_equal(expected_series, actual_series, check_names=False)

    def _assert_last_prices_are_correct_with_end_date(self, curr_time_str, end_date, expected_values, frequency):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        end_date = str_to_date(end_date, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        expected_series = PricesSeries(data=expected_values, index=self.tickers)
        actual_series = self.data_handlers[frequency].get_last_available_price(self.tickers, end_time=end_date)
        assert_series_equal(expected_series, actual_series, check_names=False)

    def _assert_get_prices_are_correct(self, curr_time_str, start_date, end_date, tickers, fields, expected_result, frequency):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        actual_prices = self.data_handlers[frequency].get_price(tickers, fields, start_date, end_date)
        self.assertEqual(type(expected_result), type(actual_prices))

        if isinstance(expected_result, QFSeries):
            assert_series_equal(expected_result, actual_prices, check_names=True)
        elif isinstance(expected_result, QFDataFrame):
            assert_dataframes_equal(expected_result, actual_prices, check_names=True)
        elif isinstance(expected_result, QFDataArray):
            assert_dataarrays_equal(expected_result, actual_prices, check_names=True)
        elif isnull(expected_result):
            self.assertTrue(isnull(actual_prices))
        else:
            self.assertEqual(expected_result, actual_prices)

    def _create_price_provider_mock(self, tickers, frequency):

        if frequency == Frequency.MIN_1:
            dates = concatenate([
                date_range(start=datetime(2009, 12, 30, 7, 57), end=datetime(2009, 12, 30, 8, 3),
                           freq=frequency.to_pandas_freq()),
                date_range(start=datetime(2009, 12, 30, 15, 57), end=datetime(2009, 12, 30, 16, 3),
                           freq=frequency.to_pandas_freq())])
        elif frequency == Frequency.MIN_5:
            dates = concatenate([
                date_range(start=datetime(2009, 12, 30, 7, 45), end=datetime(2009, 12, 30, 8, 15),
                           freq=frequency.to_pandas_freq()),
                date_range(start=datetime(2009, 12, 30, 15, 45), end=datetime(2009, 12, 30, 16, 15),
                           freq=frequency.to_pandas_freq())])
        elif frequency == Frequency.MIN_60:
            dates = concatenate([
                date_range(start=datetime(2009, 12, 30, 5), end=datetime(2009, 12, 30, 11),
                           freq=frequency.to_pandas_freq()),
                date_range(start=datetime(2009, 12, 30, 13), end=datetime(2009, 12, 30, 19),
                           freq=frequency.to_pandas_freq())])
        else:
            raise NotImplementedError(f'Frequency {frequency} is not supported')

        mock_data_array = QFDataArray.create(
            dates=dates,
            tickers=tickers,
            fields=PriceField.ohlcv(),
            data=[
                # date time_min_freq / time_5_freq / time_1h_freq
                # 2009-12-30 7 57 / 7 45 / 5 00
                [
                    # Open High  Low   Close Volume
                    [nan, nan, nan, nan, nan],  # MSFT
                    [31.2, 32.1, 31.2, 32.1, 5.1]  # AAPL
                ],
                # 2009-12-30 7 58 / 7 50 / 6 00
                [
                    # Open High  Low   Close Volume
                    [41.2, 42.0, 41.2, 42.0, 8.2],  # MSFT
                    [32.2, 32.3, 32.2, 32.3, 5.2]  # AAPL
                ],
                # 2009-12-30 7 59 / 7 55 / 7 00
                [
                    # Open High  Low   Close Volume
                    [42.3, 43.1, 42.3, 43.1, 8.3],  # MSFT
                    [33.3, 33.3, 33.2, 33.2, 5.3]  # AAPL
                ],
                # 2009-12-30 8 00 / 8 00 / 8 00
                [
                    # Open High  Low   Close Volume
                    [43.4, 45.0, 43.4, 45.0, 8.1],  # MSFT
                    [nan, nan, nan, nan, nan]  # AAPL
                ],
                # 2009-12-30 8 01 / 8 05 / 9 00
                [
                    # Open High  Low   Close Volume
                    [48.5, 49.0, 48.5, 49.0, 8.9],  # MSFT
                    [34.5, 34.5, 33.1, 33.1, 4.9]  # AAPL
                ],
                # 2009-12-30 8 02 / 8 10 / 10 00
                [
                    # Open High  Low   Close Volume
                    [49.6, 52.2, 49.6, 52.2, 8.7],  # MSFT
                    [34.4, 35.0, 34.4, 35.0, 4.7]  # AAPL
                ],
                # 2009-12-30 8 03 / 8 15 / 11 00
                [
                    # Open High  Low   Close Volume
                    [nan, nan, nan, nan, nan],  # MSFT
                    [34.0, 36.0, 34.0, 36.0, 5.6]  # AAPL
                ],
                # 2009-12-30 15 57 / 15 45 / 13 00
                [
                    # Open High  Low   Close Volume
                    [45.1, 45.3, 45.1, 45.3, 6.9],  # MSFT
                    [nan, nan, nan, nan, nan]  # AAPL
                ],
                # 2009-12-30 15 58 / 15 50 / 14 00
                [
                    # Open High  Low   Close Volume
                    [45.3, 45.6, 45.3, 45.6, 7.1],  # MSFT
                    [29.1, 29.2, 29.1, 29.2, 6.1]  # AAPL
                ],
                # 2009-12-30 15 59 / 15 55 / 15 00
                [
                    # Open High  Low   Close Volume
                    [nan, nan, nan, nan, nan],  # MSFT
                    [29.3, 29.7, 29.3, 29.7, 6.3]  # AAPL
                ],
                # 2009-12-30 16 00 / 16 00 / 16 00
                [
                    # Open High  Low   Close Volume
                    [nan, nan, nan, nan, nan],  # MSFT
                    [29.8, 30.1, 29.8, 30.1, 6.2]  # AAPL
                ],
                # 2009-12-30 16 01 / 16 05 / 17 00
                [
                    # Open High  Low   Close Volume
                    [45.6, 46.2, 45.6, 46.2, 7.3],  # MSFT
                    [30.1, 30.3, 30.1, 30.3, 6.5]  # AAPL
                ],
                # 2009-12-30 16 02 / 16 10 / 18 00
                [
                    # Open High  Low   Close Volume
                    [45.7, 45.7, 45.65, 45.65, 7.2],  # MSFT
                    [nan, nan, nan, nan, nan]  # AAPL
                ],
                # 2009-12-30 16 03 / 16 15 / 19 00
                [
                    # Open High  Low   Close Volume
                    [45.8, 45.8, 45.5, 45.5, 7.7],  # MSFT
                    [30.4, 30.7, 30.4, 30.7, 7.1]  # AAPL
                ]
            ]
        )

        def get_price(t, fields, start_date, end_date, frequency):
            got_single_date = start_date + frequency.time_delta() > end_date
            fields, got_single_field = convert_to_list(fields, PriceField)
            t, got_single_ticker = convert_to_list(t, Ticker)

            return normalize_data_array(mock_data_array.loc[start_date:end_date, t, fields], t, fields,
                                        got_single_date, got_single_ticker, got_single_field, use_prices_types=True)

        def get_last_available_price(t, freq, end_time: datetime = None):
            open_prices = mock_data_array.loc[:, t, PriceField.Open].to_pandas()
            open_prices.index = [ind for ind in open_prices.index]
            close_prices = mock_data_array.loc[:, t, PriceField.Close].to_pandas()
            close_prices.index = [ind + freq.time_delta() + RelativeDelta(microseconds=-1) for ind in close_prices.index]
            prices = PricesDataFrame(concat([open_prices, close_prices])).sort_index().ffill()

            end_date = end_time + RelativeDelta(second=0, microsecond=0)
            prices = prices.loc[:end_date + freq.time_delta() + RelativeDelta(microseconds=-1)]
            return prices.iloc[-1] if not prices.empty else PricesSeries(index=t, data=nan)

        price_data_provider_mock = Mock(spec=DataProvider, frequency=frequency)
        price_data_provider_mock.get_price.side_effect = get_price
        price_data_provider_mock.get_last_available_price.side_effect = get_last_available_price
        return price_data_provider_mock


if __name__ == '__main__':
    unittest.main()
