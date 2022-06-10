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

from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.series.qf_series import QFSeries


def list_of_max_drawdowns(prices_tms: QFSeries) -> (List[float], List[float]):
    """
    Finds the values of individual maximum drawdowns and the duration of each drawdown.

    Parameters
    ----------
    prices_tms: QFSeries
        timeseries of prices

    Returns
    -------
    List[float], List[float]
        (max_drawdowns, duration_of_drawdowns) - list of all maximum values in individual drawdowns, list of all
        durations of drawdowns expressed in days
    """

    drawdown_timeseries = drawdown_tms(prices_tms)

    max_drawdowns = []
    duration_of_drawdowns = []

    dd_start_date = None
    series_sample = []

    for date, value in drawdown_timeseries.iteritems():
        if value == 0:
            if series_sample:  # empty sequence returns false
                max_drawdowns.append(max(series_sample))
                duration_of_drawdowns.append(date - dd_start_date)

            series_sample = []  # reset the sample series
            dd_start_date = date
        else:
            series_sample.append(value)

    if series_sample:  # the last element was not added if the drawdown did not recovered
        max_drawdowns.append(max(series_sample))
        duration_of_drawdowns.append(drawdown_timeseries.index[-1] - dd_start_date)

    # convert the duration of drawdown to float value expressed in days
    duration_of_drawdowns = list(map(to_days, duration_of_drawdowns))

    return max_drawdowns, duration_of_drawdowns
