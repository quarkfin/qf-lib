from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.containers.series.qf_series import QFSeries


def get_volatility(qf_series: QFSeries, frequency: Frequency=None, annualise: bool=True) -> float:
    """
    Calculates a volatility for the given series of returns.

    Parameters
    ----------
    qf_series
        series of prices/returns (as numbers, e.g. 0.5 corresponds to 50% return)
    frequency
        the frequency of samples in the returns series; it is only obligatory to specify frequency if the annualise
        parameter is set to True, which is a default value
    annualise
        True if the volatility values should be annualised; False otherwise. If it is set to True, then it is obligatory
        to specify a frequency of the returns series.

    Returns
    -------
    volatility:
        volatility for the whole series.
    """
    returns_tms = qf_series.to_log_returns()
    assert not annualise or frequency is not None

    volatility = returns_tms.std()

    if annualise:
        volatility = annualise_with_sqrt(volatility, frequency)

    return volatility
