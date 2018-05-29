from enum import Enum

from qf_lib.containers.series.qf_series import QFSeries


class Method(Enum):
    KEEP_FIRST = 1  # Keep the first occurrence of the value
    KEEP_LAST = 2  # Keep the last occurrence of the value


def drop_consecutive_duplicates(series: QFSeries, method) -> QFSeries:
    """
    Removes consecutive duplicates (e.g. 3 consecutive 1 values should be merged into one
    with a date of the first/last occurrence in the series).

    Parameters
    ----------
    series
        series from which the consecutive duplicates should be removed
    method
        Method.KEEP_FIRST: keep the first occurrence
        Method.KEEP_LAST: keep the last occurrence

    Returns
    -------
    the series of the first occurrences of the values in each of consecutive series of same values

    Example:
    original series:
        2010-01-01 True
        2010-01-02 False
        2010-01-03 False
        2010-01-04 False
        2010-01-05 True
        2010-01-06 True
        2010-01-07 False
        2010-01-08 False
    after removing duplicates:
        2010-01-01 True
        2010-01-02 False
        2010-01-05 True
        2010-01-07 False
    """
    if method == Method.KEEP_FIRST:
        shift = 1
    elif method == Method.KEEP_LAST:
        shift = -1
    else:
        raise ValueError("Incorrect method: {:s}".format(str(method)))

    is_not_duplicate_series = series.shift(shift) != series
    no_duplicates_series = series.loc[is_not_duplicate_series]

    return no_duplicates_series
