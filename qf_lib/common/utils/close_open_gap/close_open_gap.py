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
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def close_open_gap(prices_df: PricesDataFrame, initial_price: int = 1, transaction_cost_percentage: float = 0,
                   transaction_cost_value: float = 0) -> PricesSeries:
    """Calculates price changes during the night gap (opening price compared to closing price from the
    previous day). May be interpreted as performance of strategy based on buying at close and selling at next open.

    Parameters
    ----------
    prices_df
        PricesDataFrame of at least 2 series: PriceField.Open and PriceField.Close
    initial_price
        initial price of the timeseries. If no price will be specified, then it will be assumed to be 1.
    transaction_cost_percentage
        cost of a single transaction [%]; percentage of the transaction value
        by default set to 0
        can't have a non-zero value if transaction_cost_value is set!
    transaction_cost_value
        cost of a single transaction [currency of examined asset]
        by default set to 0
        can't have a non-zero value if transaction_cost_percentage is set!

    Returns
    -------
    PricesSeries
        price changes

    """

    assert prices_df.num_of_rows > 1
    assert transaction_cost_percentage >= 0 and transaction_cost_value >= 0
    assert not (transaction_cost_percentage > 0 and transaction_cost_value > 0)  # only one type may be used

    o1 = prices_df[PriceField.Open]
    c0 = prices_df[PriceField.Close].shift(1)

    sell_price = o1
    buy_price = c0

    if transaction_cost_value > 0:
        sell_price = o1 - transaction_cost_value
        buy_price = c0 + transaction_cost_value

    elif transaction_cost_percentage > 0:
        sell_price = o1 * (1 - transaction_cost_percentage / 100)
        buy_price = c0 * (1 + transaction_cost_percentage / 100)

    ret_tms = (sell_price / buy_price) - 1
    ret_tms = cast_series(ret_tms.iloc[1:], SimpleReturnsSeries)
    prices_tms = ret_tms.to_prices(initial_price)

    return prices_tms
