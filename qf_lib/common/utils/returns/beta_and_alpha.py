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

from typing import Union, Tuple

import scipy.stats as stats

from qf_lib.containers.series.qf_series import QFSeries

SimpleStats = Tuple[float, float]
FullStats = Tuple[float, float, float, float, float]
BetaAlphaStats = Union[SimpleStats, FullStats]


def beta_and_alpha_full_stats(
        strategy_tms: QFSeries, benchmark_tms: QFSeries) -> Tuple[float, float, float, float, float]:
    """
    Calculates alpha and beta of the series versus the benchmark series.

    Parameters
    ----------
    strategy_tms: QFSeries
        Series of portfolio's returns/values
    benchmark_tms: QFSeries
        Series of benchmark returns/values

    Returns
    -------
    Tuple[float, float, float, float, float]
        (beta, alpga, r_value, p_value, std_err)

        - beta - beta coefficient for the linear fit
        - alpha - alpha coefficient for the linear fit (y = alpha * x + beta, where x is the benchmark return and y is the portfolio's return)
        - r_value - correlation coefficient. NOTE: this is not r_squared, r_squared = r_value**2
        - p_value - two-sided p-value for a hypothesis test whose null hypothesis is that the slope is zero
        - std_err - standard error of the estimate
    """
    strategy_tms = strategy_tms.to_simple_returns()
    benchmark_tms = benchmark_tms.to_simple_returns()

    from qf_lib.common.utils.dateutils.get_values_common_dates import get_values_for_common_dates
    strategy_tms, benchmark_tms = get_values_for_common_dates(strategy_tms, benchmark_tms, remove_nans=True)

    strategy_returns = strategy_tms.values
    benchmark_returns = benchmark_tms.values

    beta, alpha, r_value, p_value, std_err = stats.linregress(benchmark_returns, strategy_returns)

    return beta, alpha, r_value, p_value, std_err


def beta_and_alpha(strategy_tms: QFSeries, benchmark_tms: QFSeries) -> Tuple[float, float]:
    """
    Calculates alpha and beta of the series versus the benchmark series.
    See: beta_and_alpha_full_stats()
    """
    beta, alpha, _, _, _ = beta_and_alpha_full_stats(strategy_tms, benchmark_tms)
    return beta, alpha
