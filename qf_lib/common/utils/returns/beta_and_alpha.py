from typing import Union, Tuple

import scipy.stats as stats

from qf_lib.containers.series.qf_series import QFSeries

SimpleStats = Tuple[float, float]
FullStats = Tuple[float, float, float, float, float]
BetaAlphaStats = Union[SimpleStats, FullStats]


def beta_and_alpha_full_stats(
        strategy_tms: QFSeries, benchmark_tms: QFSeries
) -> Tuple[float, float, float, float, float]:
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
    beta: float
        beta coefficient for the linear fit
    alpha: float
        alpha coefficient for the linear fit
        (y = alpha * x + beta, where x is the benchmark return and y is the portfolio's return)
    r_value: float
        correlation coefficient. NOTE: this is not r_squared, r_squared = r_value**2
    p_value: float
        two-sided p-value for a hypothesis test whose null hypothesis is that the slope is zero
    std_err: float
        standard error of the estimate
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
