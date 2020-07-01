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

from statistics import mean

from qf_lib.containers.series.qf_series import QFSeries


def avg_drawdown_duration(prices_tms: QFSeries) -> float:
    """
    Finds the average duration of a drawdown for the given timeseries of prices.

    Parameters
    ----------
    prices_tms: QFSeries
        timeseries of prices

    Returns
    -------
    float
        average duration of a drawdown for the given timeseries of prices expressed in days
    """
    from qf_lib.common.utils.returns.list_of_max_drawdowns import list_of_max_drawdowns
    series_of_max_drawdowns, duration_of_drawdowns = list_of_max_drawdowns(prices_tms)

    if len(duration_of_drawdowns) > 0:
        return mean(duration_of_drawdowns)
    else:
        return 0.0
