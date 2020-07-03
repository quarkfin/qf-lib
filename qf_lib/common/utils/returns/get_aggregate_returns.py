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

from calendar import monthrange
from datetime import datetime

from pandas import DatetimeIndex

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.iso_to_gregorian import iso_to_gregorian
from qf_lib.common.utils.returns.index_grouping import get_grouping_for_frequency
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def get_aggregate_returns(series: QFSeries, convert_to: Frequency, multi_index: bool = False, keep_nans: bool = False) \
        -> SimpleReturnsSeries:
    """
    Aggregates returns by week, month, or year. Note: The cumulative returns function replaces all Nans with 0.000.

    Parameters
    ----------
    series: QFSeries
        Daily returns of the strategy, noncumulative.
    convert_to: Frequency
        Can be 'weekly', 'monthly', or 'yearly'.
    multi_index: bool
        Determines whether the grouping multi-index should be preserved.

    Returns
    -------
    SimpleReturnsSeries
        Aggregated returns.
    """
    simple_rets = series.to_simple_returns()
    grouping = get_grouping_for_frequency(convert_to)

    # fix for grouping with multi-index (whenever a tuple is identifying a group.
    # Example: in weekly grouping a group could be identified by a tuple (2014, 52). Then the whole series would be
    # identified by a multi-level index (dates, dates) which is forbidden (names of levels must be unique).
    # Ideally each grouping would define names of the levels, e.g. (year, week) but I don't know
    simple_rets.index.name = None
    if keep_nans:
        aggregated_series = simple_rets.groupby(grouping).apply(lambda rets: rets.total_cumulative_returns_keep_nans())
    else:
        aggregated_series = simple_rets.groupby(grouping).apply(lambda rets: rets.total_cumulative_return())

    aggregated_series = cast_series(aggregated_series, SimpleReturnsSeries)

    if not multi_index:
        # calculate a simple index based on the grouped MultiIndex
        if convert_to == Frequency.DAILY:
            # it is a day
            index = [datetime(date[2], date[1], date[0]) for date in aggregated_series.index]
        elif convert_to == Frequency.WEEKLY:
            # it is always Friday
            index = [iso_to_gregorian(date[0], date[1], 5) for date in aggregated_series.index]
        elif convert_to == Frequency.MONTHLY:
            # it is the end of the month
            index = [datetime(date[0], date[1], monthrange(date[0], date[1])[1]) for date in aggregated_series.index]
        elif convert_to == Frequency.YEARLY:
            # it is the end of the year
            index = [datetime(year, 12, 31) for year in aggregated_series.index]
        else:
            assert False

        aggregated_series = SimpleReturnsSeries(data=aggregated_series.values, index=DatetimeIndex(index))
        aggregated_series.sort_index(inplace=True)

    aggregated_series.name = series.name

    return aggregated_series
