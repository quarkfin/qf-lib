#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame


def trend_strength(prices_df: PricesDataFrame, use_next_open_instead_of_close=False):
    """
    Tells us how strongly the instrument trends during a day.
    """

    if use_next_open_instead_of_close:
        prices_df = _replace_close_by_next_open(prices_df)

    open_prices = prices_df[PriceField.Open]
    close_prices = prices_df[PriceField.Close]
    high_prices = prices_df[PriceField.High]
    low_prices = prices_df[PriceField.Low]

    numerator = close_prices / open_prices - 1
    numerator = numerator.abs()
    denominator = high_prices / low_prices - 1

    result = numerator.mean() / denominator.mean()
    return result


def down_trend_strength(prices_df: PricesDataFrame, use_next_open_instead_of_close=False):
    """
    Calculated only for down days. We study how much it moved down compared to how high it went before going down.
    High figure suggests tha we can easily short when instruments starts to go down given day
    """

    if use_next_open_instead_of_close:
        prices_df = _replace_close_by_next_open(prices_df)

    open_prices = prices_df[PriceField.Open]
    close_prices = prices_df[PriceField.Close]
    high_prices = prices_df[PriceField.High]

    is_down_day = close_prices < open_prices

    open_prices = open_prices.loc[is_down_day]
    close_prices = close_prices.loc[is_down_day]
    high_prices = high_prices.loc[is_down_day]

    numerator = open_prices / close_prices - 1
    denominator = high_prices / open_prices - 1

    if len(numerator) > 3:
        result = numerator.mean() / denominator.mean()
        return result
    return float('nan')


def up_trend_strength(prices_df: PricesDataFrame, use_next_open_instead_of_close=False):
    """
    Calculated only for up days. We study how much it moved down compared to how low it went before going down.
    High figure suggests tha we can go long when instruments starts to go up given day
    """

    if use_next_open_instead_of_close:
        prices_df = _replace_close_by_next_open(prices_df)

    open_prices = prices_df[PriceField.Open]
    close_prices = prices_df[PriceField.Close]
    low_prices = prices_df[PriceField.Low]

    is_up_day = close_prices > open_prices

    open_prices = open_prices.loc[is_up_day]
    close_prices = close_prices.loc[is_up_day]
    low_prices = low_prices.loc[is_up_day]

    numerator = open_prices / close_prices - 1  # will always be negative
    denominator = low_prices / open_prices - 1  # will always be negative

    if len(numerator) > 3:
        result = numerator.mean() / denominator.mean()
        return result
    return float('nan')


def _replace_close_by_next_open(prices_df: PricesDataFrame):
    result = prices_df.drop(columns=[PriceField.Close])
    open_prices = prices_df[PriceField.Open]
    result[PriceField.Close] = open_prices.shift(-1)  # shift to put open of next day instead of close
    result = result.drop(result.index[-1])  # remove the last row that will have a NaN
    return result
