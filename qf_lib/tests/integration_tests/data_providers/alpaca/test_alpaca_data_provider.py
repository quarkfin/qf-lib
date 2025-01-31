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
from pandas import date_range, DatetimeIndex

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.alpaca_py.alpaca_data_provider import AlpacaDataProvider, is_alpaca_intalled
from qf_lib.common.tickers.tickers import AlpacaTicker
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal, \
    assert_dataarrays_equal


@pytest.fixture
def data_provider():
    return AlpacaDataProvider()


def assert_equal(result, expected_value, decimals=2):
    try:
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
    except:
        print("A")


@pytest.mark.skipif(not is_alpaca_intalled, reason="requires alpaca-py")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_values",
    [
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", "2025-01-02", "2025-01-02", 3454.4500),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), ["close"], "2025-01-02", "2025-01-02",
         QFSeries([3454.4500], index=["close"])),
        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], "close", "2025-01-02", "2025-01-02",
         QFSeries([3454.4500], index=[AlpacaTicker("ETH/USD", SecurityType.CRYPTO)])),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), ["close"], "2025-01-02", "2025-01-06",
         QFDataFrame({"close": [3454.4500, 3595.7875, 3631.3450, 3680.5825, 3669.8150]},
                     index=date_range("2025-01-02", "2025-01-06", freq="D"))),
        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], "close", "2025-01-02", "2025-01-06",
         QFDataFrame(
             {AlpacaTicker("ETH/USD", SecurityType.CRYPTO): [3454.4500, 3595.7875, 3631.3450, 3680.5825, 3669.8150]},
             index=date_range("2025-01-02", "2025-01-06", freq="D"))),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", "2025-01-02", "2025-01-06",
         QFSeries([3454.4500, 3595.7875, 3631.3450, 3680.5825, 3669.8150],
                  date_range("2025-01-02", "2025-01-06", freq="D"))),
        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], ["close"], "2025-01-02", "2025-01-03",
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="D"),
                            [AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], ["close"],
                            [[[3454.4500]], [[3595.7875]]])),

        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO), AlpacaTicker("BTC/USD", SecurityType.CRYPTO)], "close",
         "2025-01-02", "2025-01-02",
         QFSeries([3454.4500, 96693.1250],
                  index=[AlpacaTicker("ETH/USD", SecurityType.CRYPTO), AlpacaTicker("BTC/USD", SecurityType.CRYPTO)])),
        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO), AlpacaTicker("BTC/USD", SecurityType.CRYPTO)], ["close"],
         "2025-01-02", "2025-01-03",
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="D"),
                            [AlpacaTicker("ETH/USD", SecurityType.CRYPTO),
                             AlpacaTicker("BTC/USD", SecurityType.CRYPTO)],
                            ["close"], [[[3454.4500], [96693.1250]], [[3595.7875], [98130.9775]], ])),
        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO), AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], "close",
         "2025-01-02", "2025-01-02",
         QFSeries([3454.4500, 3454.4500],
                  index=[AlpacaTicker("ETH/USD", SecurityType.CRYPTO), AlpacaTicker("ETH/USD", SecurityType.CRYPTO)])),
    ]
)
def test_get_history__daily__real_timer(tickers, fields, start_date, end_date, expected_values, data_provider):
    result = data_provider.get_history(tickers, fields, str_to_date(start_date),
                                       str_to_date(end_date))
    assert_equal(result, expected_values)


@pytest.mark.skipif(not is_alpaca_intalled, reason="requires alpaca-py")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, expected_values",
    [
        (AlpacaTicker("HAHA/USD", SecurityType.CRYPTO), "close", "2025-01-02", "2025-01-02", nan),
        (AlpacaTicker("HAHA/USD", SecurityType.CRYPTO), ["close"], "2025-01-02", "2025-01-02",
         QFSeries([nan], index=["close"])),
        ([AlpacaTicker("HAHA/USD", SecurityType.CRYPTO)], "closee", "2025-01-02", "2025-01-02",
         QFSeries([nan], index=[AlpacaTicker("HAHA/USD", SecurityType.CRYPTO)])),

        ([AlpacaTicker("HAHA/USD", SecurityType.CRYPTO), AlpacaTicker("BTC/USD", SecurityType.CRYPTO)], "close",
         "2025-01-02", "2025-01-02",
         QFSeries([nan, 96693.1250],
                  index=[AlpacaTicker("HAHA/USD", SecurityType.CRYPTO), AlpacaTicker("BTC/USD", SecurityType.CRYPTO)])),
        ([AlpacaTicker("HAHA/USD", SecurityType.CRYPTO), AlpacaTicker("BTC/USD", SecurityType.CRYPTO)], ["close"],
         "2025-01-02", "2025-01-03",
         QFDataArray.create(date_range("2025-01-02", "2025-01-03", freq="D"),
                            [AlpacaTicker("HAHA/USD", SecurityType.CRYPTO),
                             AlpacaTicker("BTC/USD", SecurityType.CRYPTO)],
                            ["close"], [[[nan], [96693.1250]], [[nan], [98130.9775]], ])),
    ]
)
def test_incorrect_inputs(tickers, fields, start_date, end_date, expected_values, data_provider):
    result = data_provider.get_history(tickers, fields, str_to_date(start_date),
                                       str_to_date(end_date))

    assert_equal(result, expected_values)


@pytest.mark.skipif(not is_alpaca_intalled, reason="requires alpaca-py")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, frequency, expected_values",
    [
        (
                AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2024, 1, 2, 14, 0),
                datetime(2024, 1, 2, 14, 1),
                Frequency.MIN_1, 2401.25),
        (
                AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 2, 14, 0),
                datetime(2025, 1, 2, 14, 3),
                Frequency.MIN_1,
                QFSeries([3462.499, 3458.600, 3454.800],
                         index=date_range(start='2025-01-02 14:00', freq='T', periods=3))),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 1), datetime(2025, 1, 7),
         Frequency.WEEKLY, 3223.9195),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 4), datetime(2025, 1, 7),
         Frequency.WEEKLY, 3223.9195),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2024, 12, 1), datetime(2024, 12, 31),
         Frequency.MONTHLY, 3340.0275),
    ]
)
def test_get_history__various_frequencies_real_timer(tickers, fields, start_date, end_date, frequency,
                                                     expected_values, data_provider):
    result = data_provider.get_history(tickers, fields, start_date, end_date, frequency)
    assert_equal(result, expected_values)


@pytest.mark.skipif(not is_alpaca_intalled, reason="requires alpaca-py")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, frequency, expected_values, current_time",
    [
        (
                AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 2, 14, 0),
                datetime(2025, 1, 2, 14, 1),
                Frequency.MIN_1,
                3462.499, datetime(2025, 1, 2, 14, 2)),
        (
                AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 2, 14, 0),
                datetime(2025, 1, 2, 14, 2),
                Frequency.MIN_1,
                QFSeries([3462.499],
                         index=date_range(start='2025-01-02 14:00', freq='T', periods=1)),
                datetime(2025, 1, 2, 14, 2)),
        (
                AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 2, 14, 0),
                datetime(2025, 1, 2, 14, 4),
                Frequency.MIN_60,
                nan, datetime(2025, 1, 2, 14, 2)),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 2, 14, 0),
         datetime(2025, 1, 2, 14, 17), Frequency.MIN_60,
         QFSeries(index=DatetimeIndex([])), datetime(2025, 1, 2, 14, 2)),

        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], "close", datetime(2025, 1, 2), datetime(2025, 1, 6),
         Frequency.DAILY,
         QFDataFrame(
             {AlpacaTicker("ETH/USD", SecurityType.CRYPTO): [3454.4500, 3595.7875, 3631.3450, 3680.5825, 3669.8150]},
             index=date_range("2025-01-02", "2025-01-06", freq="D")),
         datetime(2025, 1, 6, 15)),
        ([AlpacaTicker("ETH/USD", SecurityType.CRYPTO)], "close", datetime(2025, 1, 2), datetime(2025, 1, 3),
         Frequency.DAILY,
         QFDataFrame({AlpacaTicker("ETH/USD", SecurityType.CRYPTO): [3454.4500, 3595.7875]},
                     index=date_range("2025-01-02", "2025-01-03", freq="D")),
         datetime(2025, 1, 3, 14)),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 1), datetime(2025, 1, 7),
         Frequency.WEEKLY, 3223.9195, datetime(2025, 1, 8)),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 1), datetime(2025, 1, 7),
         Frequency.WEEKLY, nan, datetime(2025, 1, 2)),
        (AlpacaTicker("ETH/USD", SecurityType.CRYPTO), "close", datetime(2025, 1, 1), datetime(2025, 1, 7),
         Frequency.WEEKLY, 3454.4500, datetime(2025, 1, 3)),

    ]
)
def test_get_history__settable_timer(tickers, fields, start_date, end_date, frequency,
                                     expected_values, current_time, data_provider):
    MarketCloseEvent.set_trigger_time({"hour": 15, "minute": 0, "second": 0, "microsecond": 0})
    MarketOpenEvent.set_trigger_time({"hour": 9, "minute": 30, "second": 0, "microsecond": 0})

    data_provider.timer = SettableTimer(current_time)
    result = data_provider.get_history(tickers, fields, start_date, end_date, frequency)
    assert_equal(result, expected_values)
