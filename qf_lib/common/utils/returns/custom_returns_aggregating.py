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
from typing import Sequence, Callable

from qf_lib.containers.series.returns_series import ReturnsSeries, QFSeries


def aggregate_returns(
        returns: ReturnsSeries, start_dates: Sequence[datetime], end_dates: Sequence[datetime]) -> Sequence[float]:
    """
    Aggregates returns using custom start dates and end dates.

    Parameters
    ----------
    returns: ReturnsSeries
        returns to be aggregated
    start_dates: Sequence[datetime]
        list of start dates for aggregations
    end_dates: Sequence[datetime]
        list of end dates for aggregations (of the same length as start_dates)

    Returns
    -------
    Sequence[float]
        list of aggregated returns corresponding to given start dates and end dates (it has the same length)
    """
    assert len(start_dates) == len(end_dates)

    aggregated_returns = []
    for start_date, end_date in zip(start_dates, end_dates):
        series_fragment = returns.loc[start_date:end_date]
        aggregated_ret = series_fragment.total_cumulative_return()
        aggregated_returns.append(aggregated_ret)

    return aggregated_returns


def custom_series_aggregation(
        series: QFSeries, start_dates: Sequence[datetime], end_dates: Sequence[datetime], func: Callable)\
        -> Sequence[float]:
    """
    Aggregates returns using custom start dates and end dates.

    Parameters
    ----------
    series
        returns or prices to be aggregated
    start_dates
        list of start dates for aggregations
    end_dates
        list of end dates for aggregations (of the same length as start_dates)
    func
        function to be called on each slice of the data in order to aggregate it.
        It only takes one argument: slice of the series
    Returns
    -------
    list of aggregated values corresponding to given start dates and end dates (it has the same length)
    """
    assert len(start_dates) == len(end_dates)

    aggregated_values = []
    for start_date, end_date in zip(start_dates, end_dates):
        series_fragment = series.loc[start_date:end_date]
        aggregated_ret = func(series_fragment)
        aggregated_values.append(aggregated_ret)

    return aggregated_values
