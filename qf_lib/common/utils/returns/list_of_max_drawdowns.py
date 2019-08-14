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

from typing import List

from pandas import Timedelta

from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.series.qf_series import QFSeries


def list_of_max_drawdowns(prices_tms: QFSeries) -> (List[float], List[float]):
    """
    Finds the values of individual maximum drawdowns and the duration of each drawdown.

    Parameters
    ----------
    prices_tms
        timeseries of prices

    Returns
    -------
    max_drawdowns
        list of all maximum values in individual drawdowns
    duration_of_drawdowns
        list of all durations of drawdowns expressed in days
    """

    drawdown_timeseries = drawdown_tms(prices_tms)

    max_drawdowns = []
    duration_of_drawdowns = []

    series_sample = QFSeries()
    for date, value in drawdown_timeseries.iteritems():
        if value == 0:
            if not series_sample.empty:  # empty sequence returns false
                max_drawdowns.append(series_sample.max())
                time_span = series_sample.index[-1] - series_sample.index[0] + Timedelta('1 days')
                duration_of_drawdowns.append(time_span)

                series_sample = QFSeries()  # reset the sample series
        else:
            series_sample[date] = value

    if not series_sample.empty:  # the last element was not added if the drawdown did not recovered
        max_drawdowns.append(series_sample.max())
        time_span = series_sample.index[-1] - series_sample.index[0] + Timedelta('1 days')
        duration_of_drawdowns.append(time_span)

    # convert the duration of drawdown to float value expressed in days
    duration_of_drawdowns = list(map(to_days, duration_of_drawdowns))

    return max_drawdowns, duration_of_drawdowns
