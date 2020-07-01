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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.containers.series.qf_series import QFSeries


def calmar_ratio(qf_series: QFSeries, frequency: Frequency) -> float:
    """
    Calculates the Calmar ratio for a given timeseries of returns.
    calmar_ratio = CAGR / max drawdown

    Parameters
    ----------
    qf_series: QFSeries
        financial series
    frequency: Frequency
        frequency of qf_series

    Returns
    -------
    float
        calmar ratio
    """

    annualised_growth_rate = cagr(qf_series, frequency)
    max_dd = max_drawdown(qf_series)
    ratio = annualised_growth_rate / max_dd
    return ratio
