from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.returns_series import ReturnsSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def annualise_total_return(total_return: float, period_length_in_years: float, returns_type: type) -> float:
    """
    Calculates Annualised Rate of Return.

    Parameters
    ----------
    total_return: float
        return over the whole period expressed as number
    period_length_in_years: float
        time to achieve the total return, expressed in years
    returns_type: type
        type of the returns

    Returns
    -------
    annualised_return: float
        Annualised Rate of Return as number
    """
    assert issubclass(returns_type, ReturnsSeries)

    annualised_return = None
    if issubclass(returns_type, SimpleReturnsSeries):
        annualised_return = pow(1 + total_return, 1 / period_length_in_years) - 1
    elif issubclass(returns_type, LogReturnsSeries):
        annualised_return = total_return / period_length_in_years

    return annualised_return
