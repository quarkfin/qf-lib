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
from unittest.mock import patch

import pytest
import pandas as pd
from numpy import nan

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.yfinance.yfinance_data_provider import YFinanceDataProvider, is_yfinance_intalled
from qf_lib.data_providers.yfinance.yfinance_ticker import YFinanceTicker
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


@pytest.fixture
def data_provider():
    return YFinanceDataProvider()


@pytest.fixture
def mock_daily_yfinance_download():
    """ Fixture to mock yfinance.download to return hardcoded data. """

    def _mock_download(tickers, start, end, interval, keepna, progress):
        # Hardcoded data for testing
        data = {
            "AAPL": pd.DataFrame({
                ("Open", "AAPL"): [140.0, 142.0, None, 142.0, 143.0, 144.0, 145.0, 146.0],
                ("Close", "AAPL"): [150.0, 151.0, None, 152.0, 153.0, 154.0, 155.0, 156.0],
                ("Volume", "AAPL"): [1000000 + i * 100000 for i in range(8)],
            }, index=pd.date_range("2025-01-01", "2025-01-08")),
            "MSFT": pd.DataFrame({
                ("Close", "MSFT"): [300.0, None, 305.0, 310.0, 315.0, 320.0, 330.0, 340.0],
                ("Volume", "MSFT"): [2000000 + i * 100000 for i in range(8)],
            }, index=pd.date_range("2025-01-01", "2025-01-08")),
        }

        try:
            if isinstance(tickers, list):
                return pd.concat([data[t] for t in tickers], axis=1).loc[start:end]
            else:
                return data[tickers].loc[start:end]
        except KeyError:
            raise NotImplementedError(f"No data mocked for {tickers}") from None

    return _mock_download


@pytest.mark.skipif(not is_yfinance_intalled, reason="requires yfinance")
@patch("yfinance.download")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, frequency, expected_type, expected_values",
    [
        ("AAPL", "Close", "2025-01-01", "2025-01-01", Frequency.DAILY, float, 150.0),
        ("AAPL", ["Close"], "2025-01-02", "2025-01-02", Frequency.DAILY, QFSeries, QFSeries([151], index=["Close"])),
        ("AAPL", "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([150, 151], pd.date_range("2025-01-01", "2025-01-02"))),
    ]
)
def test_get_history__real_timer(mock_download, tickers, fields, start_date,
                                 end_date, frequency, expected_type, expected_values,
                                 mock_daily_yfinance_download,
                                 data_provider):
    mock_download.side_effect = mock_daily_yfinance_download

    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date), frequency)
    assert isinstance(result, expected_type), f"Expected type {expected_type}, but got {type(result)}"

    if isinstance(result, float):
        assert result == expected_values, f"Expected value {expected_values}, but got {result}"
    elif isinstance(result, QFSeries):
        assert_series_equal(expected_values, result, check_names=False, check_index_type=False)


@pytest.mark.skipif(not is_yfinance_intalled, reason="requires yfinance")
@patch("yfinance.download")
@pytest.mark.parametrize(
    "tickers, fields, start_date, end_date, frequency, expected_type, expected_values, current_time",
    [
        ("AAPL", "Close", "2025-01-01", "2025-01-01", Frequency.DAILY, float, 150.0, datetime(2025, 1, 3, 14)),
        ("AAPL", "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([150, 151], pd.date_range("2025-01-01", "2025-01-02")), datetime(2025, 1, 3, 14)),
        ("AAPL", "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([150, 151], pd.date_range("2025-01-01", "2025-01-02")), datetime(2025, 1, 2, 16)),
        ("AAPL", "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([150], pd.date_range("2025-01-01", "2025-01-01")), datetime(2025, 1, 2, 14, 45)),
        ("AAPL", "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([150], pd.date_range("2025-01-01", "2025-01-01")), datetime(2025, 1, 1, 15, 45)),

        # Get history, daily, doesn't return Open price before the market closes
        ("AAPL", "Open", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([140, ], pd.date_range("2025-01-01", "2025-01-01")), datetime(2025, 1, 2, 14)),
        ("AAPL", "Open", "2025-01-01", "2025-01-02", Frequency.DAILY, QFSeries,
         QFSeries([140, 142], pd.date_range("2025-01-01", "2025-01-02")), datetime(2025, 1, 2, 16)),

        (["AAPL", "MSFT"], "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFDataFrame,
         QFDataFrame.from_dict({YFinanceTicker('AAPL'): {str_to_date('2025-01-01'): 150.0,
                                                         str_to_date('2025-01-02'): 151.0},
                                YFinanceTicker('MSFT'): {str_to_date('2025-01-01'): 300.0,
                                                         str_to_date('2025-01-02'): nan}}),
         datetime(2025, 1, 2, 16)),
        (["AAPL", "AAPL"], "Close", "2025-01-01", "2025-01-02", Frequency.DAILY, QFDataFrame,
         QFDataFrame.from_dict({YFinanceTicker('AAPL'): {str_to_date('2025-01-01'): 150.0,
                                                         str_to_date('2025-01-02'): 151.0},
                                YFinanceTicker('AAPL'): {str_to_date('2025-01-01'): 150.0,
                                                         str_to_date('2025-01-02'): 151.0}}),
         datetime(2025, 1, 2, 16)),
    ]
)
def test_get_history__settable_timer(mock_download, tickers, fields, start_date,
                                     end_date, frequency, expected_type, expected_values, current_time,
                                     mock_daily_yfinance_download,
                                     data_provider):
    MarketOpenEvent.set_trigger_time({"hour": 9, "minute": 0, "second": 0, "microsecond": 0})
    MarketCloseEvent.set_trigger_time({"hour": 15, "minute": 0, "second": 0, "microsecond": 0})

    data_provider.timer = SettableTimer(current_time)
    mock_download.side_effect = mock_daily_yfinance_download

    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date), frequency)

    assert isinstance(result, expected_type), f"Expected type {expected_type}, but got {type(result)}"

    if isinstance(result, float):
        assert result == expected_values, f"Expected value {expected_values}, but got {result}"
    elif isinstance(result, QFSeries):
        assert_series_equal(expected_values, result, check_names=False, check_index_type=False)
