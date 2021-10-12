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

from pandas import concat

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame


def average_true_range(prices_df: PricesDataFrame, normalized: bool = False) -> float:
    """Calculates the average true range.

    Parameters
    ----------
    prices_df: PricesDataFrame
        PricesDataFrame containing High, Low, Close PriceFields and a number of rows equal to window_length + 1
    normalized: bool
        if True, each true_range is normalized to the closing price for the same day; NATR is returned
    Returns
    -------
    float
        Average True Range calculated as mean of True Range values; a time period is equal to the amount of rows
        in prices_df reduced by 1

    """
    high_tms = prices_df.loc[:, PriceField.High]
    low_tms = prices_df.loc[:, PriceField.Low]
    prev_close_tms = prices_df[PriceField.Close].shift(1)

    high_low_range = high_tms - low_tms
    high_close_range = (high_tms - prev_close_tms).abs()
    low_close_range = (low_tms - prev_close_tms).abs()

    true_range = concat([high_low_range, high_close_range, low_close_range], axis=1).max(axis=1).iloc[1:]

    if normalized:
        true_range = true_range / prev_close_tms.iloc[-1]

    return true_range.mean()
