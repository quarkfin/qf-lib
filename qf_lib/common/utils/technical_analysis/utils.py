from typing import Callable

from qf_lib.containers.series.qf_series import QFSeries


def ta_series(func: Callable, *args, **kwargs) -> QFSeries:
    """
    Function created to allow using TA-Lib functions with QFSeries.

    Parameters
    ----------
    func
        talib function: for example talib.MA
    args
        time series arguments to the function. They are all passed as QFSeries.
        for example: 'close' or 'high, low, close' where each argument is a QFSeries.
    kwargs
        additional arguments to the function. for example: 'timeperiod=10' or 'timeperiod=timeperiod, matype=i'.
        All additional arguments have to be passed as keyword arguments.

    Returns
    -------
    Output from the talib function encapsulated in a QFSeries
    """

    series_list = list(map(lambda series: series.values, args))

    result = func(*series_list, **kwargs)
    result = QFSeries(index=args[0].index, data=result)
    return result
