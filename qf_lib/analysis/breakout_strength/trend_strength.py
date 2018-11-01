from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame


def trend_strength(prices_df: PricesDataFrame):
    """
    Tells us how strongly the instrument trends during a day.
    """

    open = prices_df[PriceField.Open]
    close = prices_df[PriceField.Close]
    high = prices_df[PriceField.High]
    low = prices_df[PriceField.Low]

    numerator = close - open
    numerator = numerator.abs()
    denominator = high - low

    if len(numerator) > 3:
        result = numerator.mean() / denominator.mean()
        return result
    return float('nan')


def down_trend_strength(prices_df: PricesDataFrame):
    """"
    Calculated only for down days. We study how much it moved down compared to how high it went before going down.
    High figure suggests tha we can easily short when instruments starts to go down given day
    """
    open = prices_df[PriceField.Open]
    close = prices_df[PriceField.Close]
    high = prices_df[PriceField.High]

    is_down_day = close < open

    open = open.loc[is_down_day]
    close = close.loc[is_down_day]
    high = high.loc[is_down_day]

    numerator = open - close
    denominator = high - open

    if len(numerator) > 3:
        result = numerator.mean() / denominator.mean()
        return result
    return float('nan')


def up_trend_strength(prices_df: PricesDataFrame):
    """"
    Calculated only for up days. We study how much it moved down compared to how low it went before going down.
    High figure suggests tha we can go long when instruments starts to go up given day
    """
    open = prices_df[PriceField.Open]
    close = prices_df[PriceField.Close]
    low = prices_df[PriceField.Low]

    is_up_day = close > open

    open = open.loc[is_up_day]
    close = close.loc[is_up_day]
    high = low.loc[is_up_day]

    numerator = open - close
    denominator = high - open

    if len(numerator) > 3:
        result = numerator.mean() / denominator.mean()
        return result
    return float('nan')
