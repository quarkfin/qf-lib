from numpy import count_nonzero, mean
from pandas import Timedelta

from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.series.prices_series import PricesSeries, QFSeries


def volume_weighted_average_price(prices_tms: PricesSeries, volumes_tms: QFSeries, interval: Timedelta) -> QFSeries:
    """
    Aggregates prices in the prices_tms by calculating the average weighted price for each period. The average weighted
    prices are weighted by the volumes traded in each period.

    Parameters
    ----------
    prices_tms: PricesSeries
        timeseries of prices which should be aggregated
    volumes_tms: QFSeries
        timeseries of volumes traded; must correspond to the prices_tms
    interval: pd.Timedelta
        the length of each period from which prices should be aggregated

    Returns
    -------
    weighted_avg_price_tms: PricesSeries
        timeseries of aggregated prices; first datetimes are:
        first_price_datetime + interval, first_price_datetime + 2*interval, ..., first_price_datetime + i*interval,
        where first_price_datetime is the datetime of the first price in the original prices_tms
        The last datetime is always <= last datetime in the prices_tms
    """
    assert prices_tms.index.equals(volumes_tms.index)

    last_date = prices_tms.index[-1]
    beginning_of_window = prices_tms.index[0]
    end_of_window = beginning_of_window + interval

    weighted_avg_price_tms = PricesSeries(name=prices_tms.name)

    while end_of_window < last_date:
        prices_in_window = prices_tms.loc[beginning_of_window:end_of_window].drop([end_of_window]).values
        volumes_in_window = volumes_tms.loc[beginning_of_window:end_of_window].drop([end_of_window]).values

        # if there are no prices in the window then skip try with the next window
        if prices_in_window.size == 0:
            continue

        # if there are no volumes to use -> assume that volume in each step is the same
        if count_nonzero(volumes_in_window) == 0:
            # if all the volumes are set to 0 than assume that volume for each asset is the same
            weighted_avg_price = mean(prices_in_window)
        else:
            # calculate volume-weighted average price
            weighted_price_sum = prices_in_window.dot(volumes_in_window)
            volume_sum = sum(volumes_in_window)
            weighted_avg_price = weighted_price_sum/volume_sum

        # if the weighted average price is equal exactly 0, it means that there were missing data
        if is_finite_number(weighted_avg_price) and weighted_avg_price != 0:
            weighted_avg_price_tms[end_of_window] = weighted_avg_price

        beginning_of_window = end_of_window
        end_of_window = end_of_window + interval

    return weighted_avg_price_tms
