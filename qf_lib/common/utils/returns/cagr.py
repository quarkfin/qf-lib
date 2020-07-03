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

from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.common.utils.returns.annualise_total_return import annualise_total_return
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def cagr(qf_series: QFSeries, frequency=None):
    """
    Returns the Compound Annual Growth Rate (CAGR) calculated for the given series.

    Parameters
    ----------
    qf_series: QFSeries
        series of returns of an asset
    frequency: Frequency
        Frequency of the timeseries of returns;
        if it is None (by default) it is inferred from the timeseries of returns

    Returns
    -------
    float
        annual compound return for the given series of prices

    """
    prices_tms = qf_series.to_prices(frequency=frequency, initial_price=1.0)

    last_date = prices_tms.index[-1]
    first_date = prices_tms.index[0]
    period_length = last_date - first_date
    period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG

    total_return = prices_tms[-1] / prices_tms[0] - 1
    return annualise_total_return(
        total_return=total_return, period_length_in_years=period_length_in_years, returns_type=SimpleReturnsSeries)
