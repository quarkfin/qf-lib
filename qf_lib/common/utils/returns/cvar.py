import numpy as np

from qf_lib.containers.series.qf_series import QFSeries


def cvar(qf_series: QFSeries, percentage: float) -> float:
    """
    Calculates Conditional Value at Risk for a given percentage. Percentage equal to 0.05 means 5% CVaR.

    Parameters
    ----------
    qf_series: QFSeries
        Series of returns/prices
    percentage: float
        Percentage defining CVaR (what percentage of worst-case scenarios should be considered"

    Returns
    -------
    cvar: float
        Conditional value at risk as a number from range (-1,1). Simplifying: means how much money can be lost
        in the worst "percentage" % of all cases.
    """
    returns_tms = qf_series.to_simple_returns()
    number_of_returns = len(returns_tms.values)
    tail_length = round(number_of_returns * percentage)

    assert tail_length > 0, 'Too few values in the series'

    sorted_returns = sorted(returns_tms.values)

    tail_returns = sorted_returns[:tail_length]
    return np.mean(tail_returns, dtype=np.float64)