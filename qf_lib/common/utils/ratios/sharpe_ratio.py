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
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.qf_series import QFSeries


def sharpe_ratio(qf_series: QFSeries, frequency: Frequency, risk_free: float = 0) -> float:
    """
    Calculates the Sharpe Ratio for a given timeseries of returns and given frequency.

    Parameters
    ----------
    qf_series: QFSeries
        financial series
    frequency: Frequency
        frequency of the series
    risk_free: float
        risk free rate

    Returns
    -------
    float
        Sharpe Ratio for given series and frequency
    """
    annual_simple_return = cagr(qf_series, frequency)
    annual_log_return = np.log(annual_simple_return + 1)
    annual_vol = get_volatility(qf_series, frequency, annualise=True)

    return (annual_log_return - risk_free) / annual_vol
