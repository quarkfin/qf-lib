from numpy import std, sqrt

from qf_lib.containers.series.returns_series import ReturnsSeries


def intraday_volatility(returns: ReturnsSeries, interval_in_minutes: int) -> float:
    # TODO think how it can be merged with another function for computing volatility from returns
    # TODO test
    # second thing: the function is not used anywhere (not even in Matlab), maybe it can be deleted
    # third thing: maybe the interval could be inferred from returns dates
    """
    Calculates annualised volatility from intraday samples of given interval.

    Parameters
    ----------
    returns: ReturnsSeries
        timeseries of intraday returns
    interval_in_minutes: int
        interval between samples (in minutes)

    Returns
    -------
    intraday_volatility: float
        annualized intraday volatility calculated from intraday returns
    """
    unannualized_volatility = std(returns.values)

    minutes_in_trading_day = 390  # 6.5h * 60 min/h = 390min
    intervals_in_day = minutes_in_trading_day / interval_in_minutes
    business_days_per_year = 252

    return unannualized_volatility * sqrt(intervals_in_day * business_days_per_year)
