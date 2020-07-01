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
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.qf_series import QFSeries


def rolling_volatility(qf_series: QFSeries, frequency: Frequency = None, annualise: bool = True,
                       window_size: int = None) -> QFSeries:
    """
    Calculates the rolling volatility for the given series of returns. If the annualise parameter is set to be True,
    then it is obligatory to specify frequency.

    Parameters
    ----------
    qf_series: QFSeries
        series of returns or prices
    frequency: Frequency
        the frequency of samples in the returns series; it is only obligatory to specify frequency if the annualise
        parameter is set to True, which is a default value
    annualise: bool
        True if the volatility values should be annualised; False otherwise. If it is set to True, then it is obligatory
        to specify a frequency of the returns series.
    window_size: int
        number of samples from which the rolling volatility will be calculated. If it is not set, then only overall
        volatility (of the whole series) will be calculated

    Returns
    -------
    QFSeries
        Series of volatility values for each day concerning last window_size days.
    """
    returns_tms = qf_series.to_log_returns()
    if annualise:
        assert frequency is not None

    volatility_values = []
    for i in range(window_size - 1, len(returns_tms)):
        start_index = i - window_size + 1
        end_index = i + 1

        returns_from_window = returns_tms[start_index:end_index]
        volatility = get_volatility(returns_from_window, frequency, annualise)

        volatility_values.append(volatility)

    first_date_idx = window_size - 1
    dates = returns_tms.index[first_date_idx::]
    volatility_tms = QFSeries(data=volatility_values, index=dates)

    return volatility_tms
