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

from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.returns_series import ReturnsSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def annualise_total_return(total_return: float, period_length_in_years: float, returns_type: type) -> float:
    """
    Calculates Annualised Rate of Return.

    Parameters
    ----------
    total_return: float
        return over the whole period expressed as number
    period_length_in_years: float
        time to achieve the total return, expressed in years
    returns_type: type
        type of the returns

    Returns
    -------
    float
        Annualised Rate of Return as number
    """
    assert issubclass(returns_type, ReturnsSeries)

    annualised_return = None
    if issubclass(returns_type, SimpleReturnsSeries):
        annualised_return = pow(1 + total_return, 1 / period_length_in_years) - 1
    elif issubclass(returns_type, LogReturnsSeries):
        annualised_return = total_return / period_length_in_years

    return annualised_return
