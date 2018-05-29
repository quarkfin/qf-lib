from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.containers.series.qf_series import QFSeries


def calmar_ratio(qf_series: QFSeries, frequency: Frequency) -> float:
    """
    Calculates the Calmar ratio for a given timeseries of returns.
    calmar_ratio = CAGR / max drawdown

    Parameters
    ----------
    qf_series: financial series
    frequency: frequency of the qf_series

    Returns
    -------
    calmar_ratio: float
    """

    annualised_growth_rate = cagr(qf_series, frequency)
    max_dd = max_drawdown(qf_series)
    ratio = annualised_growth_rate / max_dd
    return ratio
