from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries


def information_ratio(portfolio: QFSeries, benchmark: QFSeries) -> float:
    """
    The function calculates information ratio based on monthly returns.
    Return of higher frequency will be aggregated into monthly.
    """
    portfolio_monthly = get_aggregate_returns(portfolio, Frequency.MONTHLY)
    benchmark_monthly = get_aggregate_returns(benchmark, Frequency.MONTHLY)

    portfolio_avg = portfolio_monthly.mean()
    benchmark_avg = benchmark_monthly.mean()

    excess_ret = portfolio_monthly - benchmark_monthly
    tracking_error = excess_ret.std()

    information_ratio_value = (portfolio_avg - benchmark_avg) / tracking_error
    return information_ratio_value
