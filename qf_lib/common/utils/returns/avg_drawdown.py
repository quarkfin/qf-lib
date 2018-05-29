from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.series.qf_series import QFSeries


def avg_drawdown(prices_tms: QFSeries) -> float:
    """
    Finds the average drawdown for the given timeseries of prices.

    Parameters
    ----------
    prices_tms: QFSeries
        timeseries of prices

    Returns
    -------
    avg_drawdown: float
        average drawdown for the given timeseries of prices expressed as the percentage value (e.g. 0.5 corresponds
        to the 50% drawdown)
    """

    return drawdown_tms(prices_tms).mean()

