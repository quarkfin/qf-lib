from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.qf_series import QFSeries


def sorino_ratio(qf_series: QFSeries, frequency: Frequency, risk_free: float=0) -> float:
    """
    Calculates the Sorino ratio for a given timeseries of returns.
    sorino_ratio = (CAGR - risk free) / annualised downside volatility

    Parameters
    ----------
    qf_series: financial series
    frequency: frequency of the qf_series

    Returns
    -------
    sorino_ratio: float
    """

    annualised_growth_rate = cagr(qf_series, frequency)
    negative_returns = qf_series[qf_series < 0]
    annualised_downside_vol = get_volatility(negative_returns, frequency, annualise=True)

    ratio = (annualised_growth_rate - risk_free) / annualised_downside_vol
    return ratio
