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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.yfinance.yfinance_data_provider import YFinanceDataProvider
from qf_lib.data_providers.yfinance.yfinance_ticker import YFinanceTicker
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal, \
    assert_dataarrays_equal


@pytest.fixture
def data_provider():
    return YFinanceDataProvider()


@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_type, expected_values",
    [
        ("AAPL", "Close", "2025-01-02", "2025-01-02", float, 243.85),
        ("AAPL", ["Close"], "2025-01-02", "2025-01-02", QFSeries, QFSeries([243.85], index=["Close"])),
        (["AAPL"], "Close", "2025-01-02", "2025-01-02", QFSeries, QFSeries([243.85], index=[YFinanceTicker("AAPL")])),
        ("AAPL", ["Close"], "2025-01-02", "2025-01-06", QFDataFrame,
         QFDataFrame({"Close": [243.85, 243.36, 245.00]}, index=date_range("2025-01-02", "2025-01-06", freq="B"))),
        (["AAPL"], "Close", "2025-01-02", "2025-01-06", QFDataFrame,
         QFDataFrame({YFinanceTicker("AAPL"): [243.85, 243.36, 245.00]}, index=date_range("2025-01-02", "2025-01-06", freq="B"))),
        ("AAPL", "Close", "2025-01-01", "2025-01-06", QFSeries,
         QFSeries([243.85, 243.36, 245.00], date_range("2025-01-02", "2025-01-06", freq="B"))),
        (["AAPL"], ["Close"], "2025-01-01", "2025-01-06", QFDataArray,
         QFDataArray.create(date_range("2025-01-02", "2025-01-06", freq="B"), [YFinanceTicker("AAPL")], ["Close"],
                            [[[243.85]], [[243.36]], [[245.00]]])),

        (["AAPL", "MSFT"], "Close", "2025-01-02", "2025-01-02", QFSeries,
         QFSeries([243.85, 418.58], index=YFinanceTicker.from_string(["AAPL", "MSFT"]))),
        (["AAPL", "MSFT"], ["Close"], "2025-01-02", "2025-01-03", QFDataArray,
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="B"), YFinanceTicker.from_string(["AAPL", "MSFT"]),
                            ["Close"], [[[243.85], [418.58]], [[243.36], [423.35]],])),
    ]
)
def test_get_history__daily__real_timer(tickers, fields, start_date, end_date, expected_type, expected_values,
                                 data_provider):
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date))
    assert isinstance(result, expected_type), f"Expected type {expected_type}, but got {type(result)}"

    if isinstance(result, float):
        assert_almost_equal(expected_values, result, decimal=2)
    elif isinstance(result, QFSeries):
        assert_series_equal(expected_values, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataFrame):
        assert_dataframes_equal(expected_values, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataArray):
        assert_dataarrays_equal(expected_values, result, check_names=False, check_index_type=False)

@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_type, expected_values",
    [
        ("HAHA", "Close", "2025-01-02", "2025-01-02", float, nan),
        ("HAHA", ["Close"], "2025-01-02", "2025-01-02", QFSeries, QFSeries([nan], index=["Close"])),
        (["HAHA"], "Closee", "2025-01-02", "2025-01-02", QFSeries, QFSeries([nan], index=[YFinanceTicker("HAHA")])),
       
        (["HAHA", "MSFT"], "Close", "2025-01-02", "2025-01-02", QFSeries,
         QFSeries([nan, 418.58], index=YFinanceTicker.from_string(["HAHA", "MSFT"]))),
        (["HAHA", "MSFT"], ["Close"], "2025-01-02", "2025-01-03", QFDataArray,
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="B"), YFinanceTicker.from_string(["HAHA", "MSFT"]),
                            ["Close"], [[[nan], [418.58]], [[nan], [423.35]],])),
    ]
)
def test_incorrect_inputs(tickers, fields, start_date, end_date, expected_type, expected_values, data_provider):
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date))
    assert isinstance(result, expected_type), f"Expected type {expected_type}, but got {type(result)}"

    if isinstance(result, float):
        assert isnan(result)
    elif isinstance(result, QFSeries):
        assert_series_equal(expected_values, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataFrame):
        assert_dataframes_equal(expected_values, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataArray):
        assert_dataarrays_equal(expected_values, result, check_names=False, check_index_type=False)

@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_type, frequency, expected_values",
    [
        ("AAPL", "Close", datetime(2025, 1, 2, 14, 0), datetime(2025, 1, 2, 14, 1), float, Frequency.MIN_1, 242.11),
        ("AAPL", "Close", datetime(2025, 1, 2, 14, 0), datetime(2025, 1, 2, 14, 3), QFSeries, Frequency.MIN_1,
                QFSeries([242.11, 242.07, 242.11], index=date_range(start='2025-01-02 14:00', freq='T', periods=3,
                                                                    tz='EST').tz_convert('UTC'))),

    ]
)
def test_get_history__various_frequencies_real_timer(tickers, fields, start_date, end_date, expected_type, frequency,
                                                     expected_values, data_provider):
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, start_date, end_date, frequency)
    assert isinstance(result, expected_type), f"Expected type {expected_type}, but got {type(result)}"

    if isinstance(result, float):
        assert_almost_equal(expected_values, result, decimal=2)
    elif isinstance(result, QFSeries):
        assert_series_equal(expected_values, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataFrame):
        assert_dataframes_equal(expected_values, result, check_names=False, check_index_type=False)
    elif isinstance(result, QFDataArray):
        assert_dataarrays_equal(expected_values, result, check_names=False, check_index_type=False)
