from pandas import Timedelta


def to_days(timedelta: Timedelta) -> float:
    """
    Converts Timedelta variable into number of days (expressed as float).

    Parameters
    ----------
    timedelta: Timedelta
        pandas Timedelta value

    Returns
    -------
    days: float
        number of days that corresponds to the given time delta
    """

    return timedelta / Timedelta('1 days')
