from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.qf_series import QFSeries


def rolling_volatility(qf_series: QFSeries, frequency: Frequency = None, annualise: bool = True,
                       window_size: int = None) -> QFSeries:
    """
    Calculates the rolling volatility for the given series of returns. If the annualise parameter is set to be True,
    then it is obligatory to specify frequency.

    Parameters
    ----------
    qf_series
        series of returns or prices
    frequency
        the frequency of samples in the returns series; it is only obligatory to specify frequency if the annualise
        parameter is set to True, which is a default value
    annualise
        True if the volatility values should be annualised; False otherwise. If it is set to True, then it is obligatory
        to specify a frequency of the returns series.
    window_size
        number of samples from which the rolling volatility will be calculated. If it is not set, then only overall
        volatility (of the whole series) will be calculated

    Returns
    -------
    volatility_tms
        Series of volatility values for each day concerning last window_size days.
    """
    returns_tms = qf_series.to_log_returns()
    if annualise:
        assert frequency is not None

    volatility_values = []
    for i in range(window_size - 1, len(returns_tms)):
        start_index = i - window_size + 1
        end_index = i + 1

        returns_from_window = returns_tms[start_index:end_index]
        volatility = get_volatility(returns_from_window, frequency, annualise)

        volatility_values.append(volatility)

    first_date_idx = window_size - 1
    dates = returns_tms.index[first_date_idx::]
    volatility_tms = QFSeries(data=volatility_values, index=dates)

    return volatility_tms
