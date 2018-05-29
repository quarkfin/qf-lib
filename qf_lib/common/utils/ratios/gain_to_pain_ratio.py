import numpy as np

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries


def gain_to_pain_ratio(qf_series: QFSeries) -> float:
    """
    Calculates the gain to pain ratio for a given timeseries of returns.
    gain_to_pain_ratio is calculated for monthly returns
    gain_to_pain_ratio = sum(all returns) / abs(sum(negative returns)

    Parameters
    ----------
    qf_series: QFSeries
        financial series

    Returns
    -------
    pain_to_gain : float
        < 0 is bad
        > 1 is good
        > 1.5 is exceptionally good
    """

    aggregated_series = get_aggregate_returns(qf_series, Frequency.MONTHLY, multi_index=True)
    negative_returns = aggregated_series.loc[aggregated_series < 0]
    negative_sum = np.abs(negative_returns.sum())
    if negative_sum != 0:
        gain_to_pain = aggregated_series.sum() / negative_sum
    else:
        gain_to_pain = float("inf")
    return gain_to_pain
