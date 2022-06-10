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

from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock

from numpy import nan
from pandas import date_range, isnull, Index, DatetimeIndex, concat

from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
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
from qf_lib.containers.dimension_names import FIELDS, TICKERS, DATES
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal, \
    assert_dataarrays_equal


class TestDailyDataHandler(TestCase):
    def setUp(self):
        self.timer = SettableTimer()
        self.tickers = [QuandlTicker("MSFT", "WIKI"), QuandlTicker("AAPL", "WIKI")]
        price_data_provider_mock = self._create_price_provider_mock(self.tickers)
        self.data_handler = DailyDataHandler(price_data_provider_mock, self.timer)

        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    """ Test get_last_available_price function"""

    def test_last_available_price_at_market_open(self):
        self._assert_last_prices_are_correct("2009-12-28 13:30:00.000000", [25.0, 27.0])
        self._assert_last_prices_are_correct("2009-12-29 13:30:00.000000", [26.0, 29.0])
        self._assert_last_prices_are_correct("2009-12-30 13:30:00.000000", [31.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-31 13:30:00.000000", [34.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-01 13:30:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-02 13:30:00.000000", [44.0, 54.0])

    def test_last_available_price_during_trading_hours(self):
        self._assert_last_prices_are_correct("2009-12-28 15:30:00.000000", [25.0, 27.0])
        self._assert_last_prices_are_correct("2009-12-29 15:30:00.000000", [26.0, 29.0])
        self._assert_last_prices_are_correct("2009-12-30 15:30:00.000000", [31.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-31 15:30:00.000000", [34.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-01 15:30:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-02 15:30:00.000000", [44.0, 54.0])

    def test_last_available_price_at_market_close_when_data_available_for_the_first_ticker(self):
        self._assert_last_prices_are_correct("2009-12-28 20:00:00.000000", [26.0, 28.0])
        self._assert_last_prices_are_correct("2009-12-29 20:00:00.000000", [26.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-30 20:00:00.000000", [32.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-31 20:00:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-01 20:00:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-02 20:00:00.000000", [47.0, 57.0])

    def test_last_available_price_after_market_close(self):
        self._assert_last_prices_are_correct("2009-12-28 21:00:00.000000", [26.0, 28.0])
        self._assert_last_prices_are_correct("2009-12-29 21:00:00.000000", [26.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-30 21:00:00.000000", [32.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-31 21:00:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-01 21:00:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-02 21:00:00.000000", [47.0, 57.0])

    def test_last_available_price_before_market_open(self):
        self._assert_last_prices_are_correct("2009-12-28 10:00:00.000000", [nan, nan])
        self._assert_last_prices_are_correct("2009-12-30 10:00:00.000000", [26.0, 30.0])
        self._assert_last_prices_are_correct("2009-12-31 10:00:00.000000", [32.0, 30.0])
        self._assert_last_prices_are_correct("2010-01-01 10:00:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-02 10:00:00.000000", [37.0, 44.0])
        self._assert_last_prices_are_correct("2010-01-03 10:00:00.000000", [47.0, 57.0])

    """ Test get_price function - single date, single field, single ticker """

    def test_get_price_before_market_close__single_date_single_field_single_ticker(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2009-12-29")

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-28 15:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2009-12-29 15:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)

    def test_get_price_after_market_close__single_date_single_field_single_ticker(self):
        start_date = str_to_date("2009-12-28")
        end_date = str_to_date("2009-12-28")

        expected_result = 25.0
        self._assert_get_prices_are_correct("2009-12-28 20:00:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2009-12-28 23:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2009-12-30 01:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)

    def test_get_price_before_market_close__single_date_single_field_single_ticker_empty_container(self):
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2010-01-01")

        expected_result = nan
        self._assert_get_prices_are_correct("2009-12-29 15:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)

    def test_get_price_after_market_close__single_date_single_field_single_ticker_empty_container(self):
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2010-01-01")

        expected_result = nan
        self._assert_get_prices_are_correct("2010-01-01 23:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2010-01-02 23:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)

    """ Test get_price function - single date, single field, multiple tickers """

    def test_get_price_before_market_close__single_date_single_field_multiple_tickers(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2009-12-29")

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-28 15:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2009-12-29 15:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    def test_get_price_after_market_close__single_date_single_field_multiple_tickers(self):
        start_date = str_to_date("2009-12-28")
        end_date = str_to_date("2009-12-28")

        expected_result = PricesSeries(data=[25.0, 27.0], index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-28 20:00:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2009-12-28 23:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2009-12-31 01:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    def test_get_price_before_market_close__single_date_single_field_multiple_tickers_empty_container(self):
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2009-12-29 15:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    def test_get_price_after_market_close__single_date_single_field_multiple_tickers_empty_container(self):
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesSeries(index=Index(self.tickers, name=TICKERS), name=PriceField.Open)
        self._assert_get_prices_are_correct("2010-01-01 23:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2010-01-02 23:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    """ Test get_price function - single date, multiple fields, single ticker """

    def test_get_price_before_market_close__single_date_multiple_fields_single_ticker(self):
        start_date = str_to_date("2009-12-28")
        end_date = str_to_date("2009-12-28")

        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       name=self.tickers[0].as_string())
        self._assert_get_prices_are_correct("2009-12-28 01:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result)

        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2009-12-31")
        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       name=self.tickers[1].as_string())
        self._assert_get_prices_are_correct("2009-12-31 19:30:00.000000", start_date, end_date, self.tickers[1],
                                            [PriceField.Open, PriceField.Close], expected_result)

    def test_get_price_after_market_close__single_date_multiple_fields_single_ticker(self):
        start_date = str_to_date("2009-12-28")
        end_date = str_to_date("2009-12-28")

        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       data=[25.0, 26.0], name=self.tickers[0].as_string())
        self._assert_get_prices_are_correct("2009-12-29 01:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result)

        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2009-12-31")
        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       data=[44.0, nan], name=self.tickers[1].as_string())
        self._assert_get_prices_are_correct("2010-01-01 01:30:00.000000", start_date, end_date, self.tickers[1],
                                            [PriceField.Open, PriceField.Close], expected_result)

    def test_get_price_after_market_close__single_date_multiple_fields_single_ticker_empty_container(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2009-12-29")

        expected_result = PricesSeries(index=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                       data=None, name=self.tickers[0].as_string())
        self._assert_get_prices_are_correct("2009-12-29 23:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result)
        self._assert_get_prices_are_correct("2010-01-01 01:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Close], expected_result)

    """ Test get_price function - single date, multiple fields, multiple tickers """

    def test_get_price_before_market_close__single_date_multiple_fields_multiple_tickers(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2009-12-29")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=None)
        self._assert_get_prices_are_correct("2009-12-29 15:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)
        self._assert_get_prices_are_correct("2009-12-28 15:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)

    def test_get_price_before_market_close__single_date_multiple_fields_multiple_tickers_empty_container(self):
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=None)
        self._assert_get_prices_are_correct("2010-01-01 15:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)
        self._assert_get_prices_are_correct("2009-12-28 15:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)

    def test_get_price_after_market_close__single_date_multiple_fields_multiple_tickers(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2009-12-29")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data={PriceField.Open: [nan, 29.0], PriceField.Close: [nan, 30.0]})
        self._assert_get_prices_are_correct("2009-12-29 20:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)

    def test_get_price_after_market_close__single_date_multiple_fields_multiple_tickers_empty_container(self):
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Close], name=FIELDS),
                                          index=Index(self.tickers, name=TICKERS),
                                          data=None)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)
        self._assert_get_prices_are_correct("2010-01-02 20:30:00.000000", start_date, end_date, self.tickers,
                                            [PriceField.Open, PriceField.Close], expected_result)

    """ Test get_price function - multiple dates, single field, single ticker """

    def test_get_price_before_data__multiple_dates_single_field_single_ticker(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesSeries(name=self.tickers[0].as_string(), index=DatetimeIndex([], name=DATES))
        self._assert_get_prices_are_correct("2009-12-30 15:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_single_field_single_ticker(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")

        with self.subTest("Test get_price if the current date is after the market close of the start_date"):
            expected_result = PricesSeries(data=[31.0], name=self.tickers[0].as_string(),
                                           index=DatetimeIndex([str_to_date("2009-12-30")], name=DATES))

            self._assert_get_prices_are_correct("2009-12-30 20:30:00.000000", start_date, end_date, self.tickers[0],
                                                PriceField.Open, expected_result)
            self._assert_get_prices_are_correct("2009-12-31 19:30:00.000000", start_date, end_date, self.tickers[0],
                                                PriceField.Open, expected_result)

            expected_result = PricesSeries(name=self.tickers[1].as_string(), index=DatetimeIndex([], name=DATES))
            self._assert_get_prices_are_correct("2009-12-30 20:30:00.000000", start_date, end_date, self.tickers[1],
                                                PriceField.Open, expected_result)

        with self.subTest("Test get_price if the current date is after the market close of the second day in the range "
                          "between start_date and end_date"):
            expected_result = PricesSeries(data=[31.0, 34.0], name=self.tickers[0].as_string(),
                                           index=DatetimeIndex([str_to_date("2009-12-30"), str_to_date("2009-12-31")],
                                                               name=DATES))
            self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers[0],
                                                PriceField.Open, expected_result)
            self._assert_get_prices_are_correct("2010-01-01 15:30:00.000000", start_date, end_date, self.tickers[0],
                                                PriceField.Open, expected_result)

            expected_result = PricesSeries(data=[44.0], name=self.tickers[1].as_string(),
                                           index=DatetimeIndex([str_to_date("2009-12-31")],
                                                               name=DATES))
            self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers[1],
                                                PriceField.Open, expected_result)
            self._assert_get_prices_are_correct("2010-01-01 15:30:00.000000", start_date, end_date, self.tickers[1],
                                                PriceField.Open, expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_single_field_single_ticker_empty_container(self):
        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2010-01-02")

        expected_result = PricesSeries(name=self.tickers[1].as_string(),
                                       index=DatetimeIndex([], name=DATES))
        self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Low, expected_result)
        self._assert_get_prices_are_correct("2010-01-01 15:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Low, expected_result)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Low, expected_result)

    def test_get_price_after_market_close__multiple_dates_single_field_single_ticker(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")
        expected_result = PricesSeries(data=[31.0, 34.0], name=self.tickers[0].as_string(),
                                       index=DatetimeIndex([str_to_date("2009-12-30"), str_to_date("2009-12-31")],
                                                           name=DATES))
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2010-01-02 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            PriceField.Open, expected_result)

        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2009-12-31")
        expected_result = PricesSeries(data=[29.0, 44.0], name=self.tickers[1].as_string(),
                                       index=DatetimeIndex([str_to_date("2009-12-29"), str_to_date("2009-12-31")],
                                                           name=DATES))
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2010-01-02 20:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Open, expected_result)

    def test_get_price_after_market_close__multiple_dates_single_field_single_ticker_empty_container(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesSeries(name=self.tickers[1].as_string(), index=DatetimeIndex([], name=DATES))
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Low, expected_result)
        self._assert_get_prices_are_correct("2010-01-03 20:30:00.000000", start_date, end_date, self.tickers[1],
                                            PriceField.Low, expected_result)

    """ Test get_price function - multiple dates, single field, multiple tickers """

    def test_get_price_before_data__multiple_dates_single_field_multiple_tickers(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS), index=DatetimeIndex([], name=DATES))
        expected_result.name = PriceField.Open
        self._assert_get_prices_are_correct("2009-12-30 15:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_single_field_multiple_tickers(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-02")

        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([str_to_date("2009-12-30")], name=DATES),
                                          data=[[31.0, nan]])
        expected_result.name = PriceField.Open
        self._assert_get_prices_are_correct("2009-12-30 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([str_to_date("2009-12-30"), str_to_date("2009-12-31")],
                                                              name=DATES),
                                          data=[[31.0, nan], [34.0, 44.0]])
        expected_result.name = PriceField.Open
        self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_single_field_multiple_tickers_empty_container(self):
        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2010-01-02")

        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS), index=DatetimeIndex([], name=DATES))
        expected_result.name = PriceField.Low
        self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Low, expected_result)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Low, expected_result)

    def test_get_price_after_market_close__multiple_dates_single_field_multiple_tickers(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-02")

        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS),
                                          index=DatetimeIndex([str_to_date("2009-12-30"), str_to_date("2009-12-31"),
                                                               str_to_date("2010-01-02")], name=DATES),
                                          data=[[31.0, nan], [34.0, 44.0], [44.0, 54.0]])
        expected_result.name = PriceField.Open
        self._assert_get_prices_are_correct("2010-01-02 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)
        self._assert_get_prices_are_correct("2010-01-05 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Open, expected_result)

    def test_get_price_after_market_close__multiple_dates_single_field_multiple_tickers_empty_container(self):
        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index(self.tickers, name=TICKERS), index=DatetimeIndex([], name=DATES))
        expected_result.name = PriceField.Low
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Low, expected_result)
        self._assert_get_prices_are_correct("2010-01-05 20:30:00.000000", start_date, end_date, self.tickers,
                                            PriceField.Low, expected_result)

    """ Test get_price function - multiple dates, multiple fields, single ticker """

    def test_get_price_before_data__multiple_dates_multiple_fields_single_ticker(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([], name=DATES))
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 15:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_multiple_fields_single_ticker(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2010-01-02")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([], name=DATES),
                                          data={PriceField.Open: []})
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-29 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Low], name=FIELDS),
                                          index=DatetimeIndex([str_to_date("2009-12-29")], name=DATES),
                                          data={PriceField.Open: [nan], PriceField.Low: [17.0]})
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-29 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Low], expected_result)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Low], name=FIELDS),
                                          index=DatetimeIndex([str_to_date("2009-12-29"), str_to_date("2009-12-30")],
                                                              name=DATES),
                                          data={PriceField.Open: [nan, 31.0], PriceField.Low: [17.0, 31.2]})
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Low], expected_result)

        expected_result = PricesDataFrame(columns=Index([PriceField.Open], name=FIELDS),
                                          index=DatetimeIndex([str_to_date("2009-12-30")],
                                                              name=DATES),
                                          data={PriceField.Open: [31.0]})
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-30 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open], expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_multiple_fields_single_ticker_empty_container(self):
        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2010-01-02")

        expected_result = PricesDataFrame(columns=Index([PriceField.Low], name=FIELDS),
                                          index=DatetimeIndex([], name=DATES))
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Low], expected_result)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Low], expected_result)

    def test_get_price_after_market_close__multiple_dates_multiple_fields_single_ticker(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index([PriceField.Open, PriceField.Low], name=FIELDS),
                                          index=DatetimeIndex([str_to_date("2009-12-29"), str_to_date("2009-12-30"),
                                                               str_to_date("2009-12-31")],
                                                              name=DATES),
                                          data={PriceField.Open: [nan, 31.0, 34.0], PriceField.Low: [17.0, 31.2, nan]})
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Low], expected_result)
        self._assert_get_prices_are_correct("2010-01-02 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Open, PriceField.Low], expected_result)

    def test_get_price_after_market_close__multiple_dates_multiple_fields_single_ticker_empty_container(self):
        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2010-01-01")

        expected_result = PricesDataFrame(columns=Index([PriceField.Low], name=FIELDS),
                                          index=DatetimeIndex([], name=DATES))
        expected_result.name = self.tickers[0].as_string()
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Low], expected_result)
        self._assert_get_prices_are_correct("2010-01-05 20:30:00.000000", start_date, end_date, self.tickers[0],
                                            [PriceField.Low], expected_result)

    """ Test get_price function - multiple dates, multiple fields, multiple tickers """

    def test_get_price_before_data__multiple_dates_multiple_fields_multiple_tickers(self):
        start_date = str_to_date("2009-12-30")
        end_date = str_to_date("2010-01-01")
        fields = [PriceField.Open]

        dates = date_range(start_date, end_date, freq="D")
        expected_result = QFDataArray.create(dates, self.tickers, fields, data=None)
        expected_result = normalize_data_array(expected_result, self.tickers, fields, False, False, False)

        self._assert_get_prices_are_correct("2009-12-30 15:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_multiple_fields_multiple_tickers(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2010-01-01")
        fields = [PriceField.High]

        expected_result = QFDataArray.create([str_to_date("2009-12-30")], self.tickers, fields, data=[[[31.1], [nan]]])
        self._assert_get_prices_are_correct("2009-12-30 20:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)
        self._assert_get_prices_are_correct("2009-12-31 15:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)

        expected_result = QFDataArray.create([str_to_date("2009-12-30"), str_to_date("2009-12-31")], self.tickers,
                                             fields, data=[[[31.1], [nan]], [[35.1], [45.1]]])
        self._assert_get_prices_are_correct("2009-12-31 20:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)

    def test_get_price_before_last_date_market_close__multiple_dates_multiple_fields_multiple_tickers_empty_container(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2010-01-01")
        fields = [PriceField.High]

        dates = date_range(start_date, end_date, freq="D")
        expected_result = QFDataArray.create(dates, self.tickers, fields, data=None)
        expected_result = normalize_data_array(expected_result, self.tickers, fields, False, False, False)
        self._assert_get_prices_are_correct("2009-12-29 20:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)

    def test_get_price_after_market_close__multiple_dates_multiple_fields_multiple_tickers(self):
        start_date = str_to_date("2009-12-29")
        end_date = str_to_date("2010-01-01")
        fields = [PriceField.High]

        expected_result = QFDataArray.create([str_to_date("2009-12-30"), str_to_date("2009-12-31")], self.tickers,
                                             fields, data=[[[31.1], [nan]], [[35.1], [45.1]]])
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)
        self._assert_get_prices_are_correct("2010-01-05 20:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)

    def test_get_price_after_market_close__multiple_dates_multiple_fields_multiple_tickers_empty_container(self):
        start_date = str_to_date("2009-12-31")
        end_date = str_to_date("2010-01-01")
        fields = [PriceField.Low]

        dates = date_range(start_date, end_date, freq="D")
        expected_result = QFDataArray.create(dates, self.tickers, fields, data=None)
        expected_result = normalize_data_array(expected_result, self.tickers, fields, False, False, False)
        self._assert_get_prices_are_correct("2010-01-01 20:30:00.000000", start_date, end_date, self.tickers,
                                            fields, expected_result)

    def _assert_last_prices_are_correct(self, curr_time_str, expected_values):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        expected_series = PricesSeries(data=expected_values, index=self.tickers)
        actual_series = self.data_handler.get_last_available_price(self.tickers)
        assert_series_equal(expected_series, actual_series, check_names=False)

    def _assert_get_prices_are_correct(self, curr_time_str, start_date, end_date, tickers, fields, expected_result):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)

        actual_prices = self.data_handler.get_price(tickers, fields, start_date, end_date)
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

    def _create_price_provider_mock(self, tickers):
        mock_data_array = QFDataArray.create(
            dates=date_range(start='2009-12-28', end='2010-01-02', freq='D'),
            tickers=tickers,
            fields=PriceField.ohlcv(),
            data=[
                # 2009-12-28
                [
                    # Open High  Low   Close Volume
                    [25.0, 25.1, 25.2, 26.0, 25.3],  # MSFT
                    [27.0, 27.1, 27.2, 28.0, 27.3]  # AAPL
                ],
                # 2009-12-29
                [
                    # Open High  Low   Close Volume
                    [nan, nan, 17.0, nan, nan],  # MSFT
                    [29.0, nan, 29.2, 30.0, 29.3]  # AAPL
                ],
                # 2009-12-30
                [
                    # Open High  Low   Close Volume
                    [31.0, 31.1, 31.2, 32.0, 31.3],  # MSFT
                    [nan, nan, nan, nan, nan]  # AAPL
                ],
                # 2009-12-31
                [
                    # Open High  Low   Close Volume
                    [34.0, 35.1, nan, 37.0, 39.3],  # MSFT
                    [44.0, 45.1, nan, nan, 49.3]  # AAPL
                ],
                # 2010-01-01
                [
                    # Open High  Low   Close Volume
                    [nan, nan, nan, nan, nan],  # MSFT
                    [nan, nan, nan, nan, nan]  # AAPL
                ],
                # 2010-01-02
                [
                    # Open High  Low   Close Volume
                    [44.0, 45.1, 43.2, 47.0, 49.3],  # MSFT
                    [54.0, 55.1, 53.2, 57.0, 59.3]  # AAPL
                ]
            ]
        )

        def get_price(t, fields, start_time, end_time, _):
            got_single_date = start_time.date() == end_time.date()
            fields, got_single_field = convert_to_list(fields, PriceField)
            t, got_single_ticker = convert_to_list(t, Ticker)

            return normalize_data_array(mock_data_array.loc[start_time:end_time, t, fields], t, fields,
                                        got_single_date, got_single_ticker, got_single_field, use_prices_types=True)

        def get_last_available_price(t, _, end_time: datetime = None):
            open_prices = mock_data_array.loc[:, t, PriceField.Open].to_pandas()
            open_prices.index = [ind + MarketOpenEvent.trigger_time() for ind in open_prices.index]
            close_prices = mock_data_array.loc[:, t, PriceField.Close].to_pandas()
            close_prices.index = [ind + MarketCloseEvent.trigger_time() for ind in close_prices.index]
            prices = PricesDataFrame(concat([open_prices, close_prices])).sort_index().ffill()

            end_date = end_time + RelativeDelta(days=1, hour=0, minute=0, second=0, microsecond=0, microseconds=-1)
            prices = prices.loc[:end_date]
            return prices.iloc[-1] if not prices.empty else PricesSeries(index=t, data=nan)

        price_data_provider_mock = Mock(spec=DataProvider, frequency=Frequency.DAILY)
        price_data_provider_mock.get_price.side_effect = get_price
        price_data_provider_mock.get_last_available_price.side_effect = get_last_available_price

        return price_data_provider_mock
