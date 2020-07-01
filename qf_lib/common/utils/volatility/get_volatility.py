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
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.containers.series.qf_series import QFSeries


def get_volatility(qf_series: QFSeries, frequency: Frequency = None, annualise: bool = True) -> float:
    """
    Calculates a volatility for the given series of returns or prices. If a PricesSeries is given,
    the calculation window is shorter by 1 due to the initial conversion into returns.

    Parameters
    ----------
    qf_series: QFSeries
        series of prices/returns (as numbers, e.g. 0.5 corresponds to 50% return)
    frequency: Frequency
        the frequency of samples in the returns series; it is only obligatory to specify frequency if the annualise
        parameter is set to True, which is a default value
    annualise: bool
        True if the volatility values should be annualised; False otherwise. If it is set to True, then it is obligatory
        to specify a frequency of the returns series.

    Returns
    -------
    float
        volatility for the whole series.
    """
    returns_tms = qf_series.to_log_returns()
    assert len(returns_tms) >= 2, "minimal num_of_rows to receive a real result is 2"
    assert not annualise or frequency is not None

    volatility = returns_tms.std()

    if annualise:
        volatility = annualise_with_sqrt(volatility, frequency)

    return volatility
