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

import numpy as np

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries


def gain_to_pain_ratio(qf_series: QFSeries) -> float:
    """
    Calculates the gain to pain ratio for a given timeseries of returns.
    gain_to_pain_ratio is calculated for monthly returns
    gain_to_pain_ratio = sum(all returns) / abs(sum(negative returns)

    Parameters
    ----------
    qf_series: QFSeries
        financial series

    Returns
    -------
    float
        < 0 is bad
        > 1 is good
        > 1.5 is exceptionally good
    """

    aggregated_series = get_aggregate_returns(qf_series, Frequency.MONTHLY, multi_index=True)
    negative_returns = aggregated_series.loc[aggregated_series < 0]
    negative_sum = np.abs(negative_returns.sum())
    if negative_sum != 0:
        gain_to_pain = aggregated_series.sum() / negative_sum
    else:
        gain_to_pain = float("inf")
    return gain_to_pain
