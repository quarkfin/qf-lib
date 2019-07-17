import numpy as np

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame


def average_true_range(prices_df: PricesDataFrame, normalized: bool = False) -> float:
    """

    Parameters
    ----------
    prices_df
        PricesDataFrame containing High, Low, Close PriceFields and a number of rows equal to window_length + 1
    normalized
        if True, each true_range is normalized to the closing price for the same day; NATR is returned
    Returns
    -------
    Average True Range calculated as mean of True Range values; a time period is equal to the amount of rows
    in prices_df reduced by 1

    """
    high_tms = prices_df[PriceField.High]
    low_tms = prices_df[PriceField.Low]
    prev_close_tms = prices_df[PriceField.Close].shift(1)

    high_low_range = high_tms - low_tms
    high_close_range = abs(high_tms - prev_close_tms)
    low_close_range = abs(low_tms - prev_close_tms)

    high_low_range = high_low_range.iloc[1:]
    high_close_range = high_close_range.iloc[1:]
    low_close_range = low_close_range.iloc[1:]

    tr_values = []
    for r1, r2, r3 in zip(high_low_range, high_close_range, low_close_range):
        true_range = max(r1, r2, r3)
        if normalized:
            true_range = true_range / prev_close_tms[-1]
        tr_values.append(true_range)

    return np.mean(tr_values).item()
