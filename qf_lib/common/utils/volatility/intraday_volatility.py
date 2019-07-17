from numpy import std, sqrt

from qf_lib.containers.series.returns_series import ReturnsSeries


def intraday_volatility(returns: ReturnsSeries, interval_in_minutes: int) -> float:
    """
    Calculates annualised volatility from intraday samples of given interval.

    Parameters
    ----------
    returns
        timeseries of intraday returns
    interval_in_minutes
        interval between samples (in minutes)

    Returns
    -------
    intraday_volatility
        annualized intraday volatility calculated from intraday returns
    """
    unannualized_volatility = std(returns.values)

    minutes_in_trading_day = 390  # 6.5h * 60 min/h = 390min
    intervals_in_day = minutes_in_trading_day / interval_in_minutes
    business_days_per_year = 252

    return unannualized_volatility * sqrt(intervals_in_day * business_days_per_year)
