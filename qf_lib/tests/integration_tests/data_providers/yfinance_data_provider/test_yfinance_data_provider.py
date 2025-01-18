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
import pytest

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.yfinance.yfinance_data_provider import YFinanceDataProvider
from qf_lib.data_providers.yfinance.yfinance_ticker import YFinanceTicker

TICKERS = ["AAPL", ["AAPL"], ["AAPL", "MSFT"]]
FIELDS = ["Close", ["Close"], ["Close", "Volume"]]
DATES = [("2025-01-02", "2025-01-02"), ("2025-01-02", "2025-01-10")]

@pytest.mark.parametrize("tickers", TICKERS)
@pytest.mark.parametrize("fields", FIELDS)
@pytest.mark.parametrize("start_date, end_date", DATES)
def test_get_price__returned_types__daily_frequency__real_timer(tickers, fields, start_date, end_date):
    data_provider = YFinanceDataProvider()
    result = data_provider.get_history(YFinanceTicker.from_string(tickers), fields, str_to_date(start_date),
                                       str_to_date(end_date), Frequency.DAILY)

    single_ticker = isinstance(tickers, str)
    single_field = isinstance(fields, str)
    single_date = start_date == end_date
    expected_dimension = 3 - sum((single_ticker, single_field, single_date))

    # Validate the type of the result
    if expected_dimension == 0:
        assert isinstance(result, (float, type(None))), "Expected float or None for a single ticker, field, and date"
    elif expected_dimension == 1:
        assert isinstance(result, QFSeries), "Expected QFSeries for single ticker with multiple fields"
    elif expected_dimension == 2:
        assert isinstance(result, QFDataFrame), "Expected QFDataFrame for multiple tickers with single field"
    else:
        assert isinstance(result, QFDataArray), "Expected QFDataArray for multiple tickers and multiple fields"

    # Validate the values if applicable
    if isinstance(result, (QFSeries, QFDataFrame, QFDataArray)):
        assert not result.dropna(how="all").empty, "Expected non-null values in the result"
    elif isinstance(result, float):
        assert result >= 0, "Expected the price to be a non-negative float"
