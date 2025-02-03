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
from cmath import isnan
from datetime import datetime

import pytest
from numpy import nan
from numpy.testing import assert_almost_equal
from pandas import date_range

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.yfinance.yfinance_data_provider import YFinanceDataProvider, is_yfinance_intalled
from qf_lib.data_providers.yfinance.yfinance_ticker import YFinanceTicker
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal, \
    assert_dataarrays_equal


@pytest.fixture
def data_provider():
    return YFinanceDataProvider()


def assert_equal(result, expected_value, decimals=2):
    expected_type = type(expected_value)
    assert isinstance(result, expected_type), f"Expected type {expected_type}, but got {type(result)}"

    if isinstance(result, float):
        if isnan(result):
            assert isnan(expected_value)
        else:
            assert_almost_equal(expected_value, result, decimal=decimals)
    elif isinstance(result, QFSeries):
        assert_series_equal(expected_value, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataFrame):
        assert_dataframes_equal(expected_value, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataArray):
        assert_dataarrays_equal(expected_value, result, check_names=False, check_index_type=False)


@pytest.mark.skipif(not is_yfinance_intalled, reason="requires yfinance")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_values",
    [
        ("AAPL", "Close", "2025-01-02", "2025-01-02", 243.85),
        ("AAPL", ["Close"], "2025-01-02", "2025-01-02", QFSeries([243.85], index=["Close"])),
        (["AAPL"], "Close", "2025-01-02", "2025-01-02", QFSeries([243.85], index=[YFinanceTicker("AAPL")])),
        ("AAPL", ["Close"], "2025-01-02", "2025-01-06",
         QFDataFrame({"Close": [243.85, 243.36, 245.00]}, index=date_range("2025-01-02", "2025-01-06", freq="B"))),
        (["AAPL"], "Close", "2025-01-02", "2025-01-06",
         QFDataFrame({YFinanceTicker("AAPL"): [243.85, 243.36, 245.00]},
                     index=date_range("2025-01-02", "2025-01-06", freq="B"))),
        ("AAPL", "Close", "2025-01-01", "2025-01-06",
         QFSeries([243.85, 243.36, 245.00], date_range("2025-01-02", "2025-01-06", freq="B"))),
        (["AAPL"], ["Close"], "2025-01-01", "2025-01-06",
         QFDataArray.create(date_range("2025-01-02", "2025-01-06", freq="B"), [YFinanceTicker("AAPL")], ["Close"],
                            [[[243.85]], [[243.36]], [[245.00]]])),

        (["AAPL", "MSFT"], "Close", "2025-01-02", "2025-01-02",
         QFSeries([243.85, 418.58], index=YFinanceTicker.from_string(["AAPL", "MSFT"]))),
        (["AAPL", "MSFT"], ["Close"], "2025-01-02", "2025-01-03",
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="B"),
                            YFinanceTicker.from_string(["AAPL", "MSFT"]),
                            ["Close"], [[[243.85], [418.58]], [[243.36], [423.35]], ])),
        (["AAPL", "AAPL"], "Close", "2025-01-02", "2025-01-02",
         QFSeries([243.85, 243.85], index=YFinanceTicker.from_string(["AAPL", "AAPL"]))),
    ]
)
def test_get_history__daily__real_timer(tickers, fields, start_date, end_date, expected_values, data_provider):
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date))
    assert_equal(result, expected_values)


@pytest.mark.skipif(not is_yfinance_intalled, reason="requires yfinance")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_values",
    [
        ("HAHA", "Close", "2025-01-02", "2025-01-02", nan),
        ("HAHA", ["Close"], "2025-01-02", "2025-01-02", QFSeries([nan], index=["Close"])),
        (["HAHA"], "Closee", "2025-01-02", "2025-01-02", QFSeries([nan], index=[YFinanceTicker("HAHA")])),

        (["HAHA", "MSFT"], "Close", "2025-01-02", "2025-01-02",
         QFSeries([nan, 418.58], index=YFinanceTicker.from_string(["HAHA", "MSFT"]))),
        (["HAHA", "MSFT"], ["Close"], "2025-01-02", "2025-01-03",
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="B"),
                            YFinanceTicker.from_string(["HAHA", "MSFT"]),
                            ["Close"], [[[nan], [418.58]], [[nan], [423.35]], ])),
    ]
)
def test_incorrect_inputs(tickers, fields, start_date, end_date, expected_values, data_provider):
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date))

    assert_equal(result, expected_values)


@pytest.mark.skipif(not is_yfinance_intalled, reason="requires yfinance")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, frequency, expected_values",
    [
        ("AAPL", "Close", datetime(2025, 1, 1), datetime(2025, 1, 7), Frequency.WEEKLY, 242.21),
        ("AAPL", "Close", datetime(2025, 1, 4), datetime(2025, 1, 7), Frequency.WEEKLY, 242.21),
        ("AAPL", "Close", datetime(2024, 12, 1), datetime(2024, 12, 31), Frequency.MONTHLY, 250.42),
    ]
)
def test_get_history__various_frequencies_real_timer(tickers, fields, start_date, end_date, frequency,
                                                     expected_values, data_provider):
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, start_date, end_date, frequency)
    assert_equal(result, expected_values)


@pytest.mark.skipif(not is_yfinance_intalled, reason="requires yfinance")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, frequency, expected_values, current_time",
    [
        (["AAPL"], "Close", datetime(2025, 1, 2), datetime(2025, 1, 6), Frequency.DAILY,
         QFDataFrame({YFinanceTicker("AAPL"): [243.85, 243.36, 245.00]},
                     index=date_range("2025-01-02", "2025-01-06", freq="B")),
         datetime(2025, 1, 6, 15)),
        (["AAPL"], "Close", datetime(2025, 1, 2), datetime(2025, 1, 6), Frequency.DAILY,
         QFDataFrame({YFinanceTicker("AAPL"): [243.85, 243.36]},
                     index=date_range("2025-01-02", "2025-01-05", freq="B")),
         datetime(2025, 1, 6, 14)),
        ("AAPL", "Close", datetime(2025, 1, 1), datetime(2025, 1, 7), Frequency.WEEKLY, 242.21, datetime(2025, 1, 8)),
        ("AAPL", "Close", datetime(2025, 1, 1), datetime(2025, 1, 7), Frequency.WEEKLY, nan, datetime(2025, 1, 2)),
        ("AAPL", "Close", datetime(2025, 1, 1), datetime(2025, 1, 7), Frequency.WEEKLY, 243.85, datetime(2025, 1, 3)),

    ]
)
def test_get_history__settable_timer(tickers, fields, start_date, end_date, frequency,
                                     expected_values, current_time, data_provider):
    MarketCloseEvent.set_trigger_time({"hour": 15, "minute": 0, "second": 0, "microsecond": 0})
    MarketOpenEvent.set_trigger_time({"hour": 9, "minute": 30, "second": 0, "microsecond": 0})

    data_provider.timer = SettableTimer(current_time)
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, start_date, end_date, frequency)
    assert_equal(result, expected_values)
