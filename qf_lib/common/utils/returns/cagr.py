from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.common.utils.returns.annualise_total_return import annualise_total_return
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def cagr(qf_series: QFSeries, frequency=None):
    """
    Returns the Compound Annual Growth Rate (CAGR) calculated for the given series.

    Parameters
    ----------
    qf_series
        series of returns of an asset
    frequency
        Frequency of the timeseries of returns;
        if it is None (by default) it is inferred from the timeseries of returns

    Returns
    -------
    annual_compound_return: float
        annual compound return for the given series of prices

    """
    prices_tms = qf_series.to_prices(frequency=frequency, initial_price=1.0)

    last_date = prices_tms.index[-1]
    first_date = prices_tms.index[0]
    period_length = last_date - first_date
    period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG

    total_return = prices_tms[-1] / prices_tms[0] - 1
    return annualise_total_return(
        total_return=total_return, period_length_in_years=period_length_in_years, returns_type=SimpleReturnsSeries)
