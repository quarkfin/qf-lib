from statistics import mean

from qf_lib.containers.series.qf_series import QFSeries


def avg_drawdown_duration(prices_tms: QFSeries) -> float:
    """
    Finds the average duration of a drawdown for the given timeseries of prices.

    Parameters
    ----------
    prices_tms
        timeseries of prices

    Returns
    -------
    avg_duration
        average duration of a drawdown for the given timeseries of prices expressed in days
    """
    from qf_lib.common.utils.returns.list_of_max_drawdowns import list_of_max_drawdowns
    series_of_max_drawdowns, duration_of_drawdowns = list_of_max_drawdowns(prices_tms)

    if len(duration_of_drawdowns) > 0:
        return mean(duration_of_drawdowns)
    else:
        return 0.0
