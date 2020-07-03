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
from typing import Sequence, Tuple

from qf_lib.common.utils.miscellaneous.consecutive_duplicates import drop_consecutive_duplicates, Method
from qf_lib.containers.series.qf_series import QFSeries


def periods_list_from_bool_series(series: QFSeries) -> Sequence[Tuple[datetime, datetime]]:
    """
    Uses a timeseries containing boolean values to create periods of True values.

    Parameters
    ----------
    series: QFSeries
        the series of boolean values

        For example:
        - 2017-01-01  True
        - 2017-01-02  False
        - 2017-01-03  True
        - 2017-01-05  False
        - 2017-01-06  True
        - 2017-01-07  True
        - 2017-01-08  False
        - 2017-01-09  True
        - 2017-01-10  True
        frequency: Frequency.DAILY

        Periods:
        - 2017-01-01 - 2017-01-02
        - 2017-01-03 - 2017-01-05
        - 2017-01-06 - 2017-01-08
        - 2017-01-09 - 2017-01-11 (end date calculated based on a frequency of the series)

    Returns
    -------
    Tuple[datetime, datetime]
        list of tuples. Each tuple corresponds to one period and consists of two dates: start date and end date
        of a period.
    """
    result = []

    first_occurrences_only = drop_consecutive_duplicates(series, Method.KEEP_FIRST)

    start_date = None
    for date, should_be_shadowed in first_occurrences_only.iteritems():
        date = date.to_pydatetime()  # convert from pandas.Timestamp

        if should_be_shadowed:
            start_date = date
        elif start_date is not None:
            result.append((start_date, date))
            start_date = None

    last_period_of_series_should_be_shadowed = start_date is not None
    if last_period_of_series_should_be_shadowed:
        end_date = _infer_end_date(series)
        result.append((start_date, end_date))

    return result


def _infer_end_date(series: QFSeries) -> datetime:
    time_delta = series.get_frequency().time_delta()
    last_series_date = series.index[-1].to_pydatetime()
    end_date = last_series_date + time_delta

    return end_date
