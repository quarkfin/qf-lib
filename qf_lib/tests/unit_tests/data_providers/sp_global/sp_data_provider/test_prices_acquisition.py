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
from datetime import datetime

import pytest
from numpy import nan
from pandas import DatetimeIndex, notna, isna

from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.sp_global.sp_field import SPField
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal


@pytest.mark.parametrize("date,expected_price", [(datetime(2011, 1, 1), 15.0), (datetime(2011, 1, 3), nan)])
def test_get_history__no_currency_data__single_price(date, expected_price, sp_data_provider):
    """
    Test single price output. Test description:
    - adjustment is set to True, but as no corporate actions exist for this ticker it does not affect the result
    - price close is fetched in the local currency (no currency parameter)
    - trading item id has no currency data in the ciqtradingitem table (currencyid is None)
    """
    price = sp_data_provider.get_history(SPTicker(2002), SPField.ClosePrice, date, date)
    assert price == expected_price if notna(expected_price) else isna(expected_price)


@pytest.mark.parametrize("adjustment", [False, True])
def test_get_history__no_currency_data__prices_series(adjustment, sp_data_provider):
    """
    Test prices series output. Test description:
    - both adjustment and lack of adjustment is tested (no corporate actions exist for this ticker but it should
    not affect the result)
    - price close is fetched in the local currency
    - trading item id has no currency data in the ciqtradingitem table (currencyid is None)
    """
    sp_data_provider.use_adjusted_prices = adjustment
    prices = sp_data_provider.get_history(SPTicker(2002), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 10))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFSeries([15.0, 16.0, 17.0, 18.0], index, name="2002")
    assert_series_equal(prices, expected_prices)


@pytest.mark.parametrize("adjustment,currency", [(False, None), (False, "USD"), (True, None), (True, "USD")])
def test_get_history__volume_series(adjustment, currency, sp_data_provider):
    """
    Test volume series output. Test description:
    - both adjustment and lack of adjustment is tested (no corporate actions exist for this ticker but it should
    not affect the result)
    - volume is fetched both with and without currency (it should not affect the result in case of volume)
    - trading item id has no currency data in the ciqtradingitem table (currencyid is None), but it shouldn't affect
    volume
    """
    sp_data_provider.use_adjusted_prices = adjustment
    volumes = sp_data_provider.get_history(SPTicker(2002), SPField.Volume, datetime(2011, 1, 1),
                                           datetime(2011, 1, 10), currency=currency)
    index = DatetimeIndex(['2011-01-01', '2011-01-04', '2011-01-05'], name="dates")
    expected_volume = QFSeries([100.0, 300.0, 400.0], index, name="2002")
    assert_series_equal(volumes, expected_volume)


def test_get_history__no_currency_data__usd_currency(sp_data_provider):
    """
    Test prices series output. Test description:
    - price close is fetched in USD
    - trading item id has no currency data in the ciqtradingitem table (currencyid is None)

    As the tradingitemid has no currency parameter attached, fetching the prices in USD should result in an empty series.
    """
    prices = sp_data_provider.get_history(SPTicker(2002), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 10), to_usd=True)
    assert prices.empty


@pytest.mark.parametrize("adjustment,currency", [(False, None), (False, "USD"), (True, None), (True, "USD")])
def test_get_history__usd_ticker(adjustment, currency, sp_data_provider):
    """
    Test volume series output. Test description:
    - both adjustment and lack of adjustment is tested (no corporate actions exist for this ticker but it should
    not affect the result)
    - prices are fetched both with and without currency (it should not affect the result as the currency of this ticker
    is USD)
    """
    sp_data_provider.use_adjusted_prices = adjustment
    prices = sp_data_provider.get_history(SPTicker(2003), SPField.ClosePrice, datetime(2011, 1, 1),
                                          datetime(2011, 1, 10), currency=currency)
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFSeries([20.0, 21.0, 22.0, 23.0], index, name="2003")
    assert_series_equal(prices, expected_prices)


@pytest.mark.parametrize("adjustment", [False, True])
def test_get_history__exchange_rate_usd_jpy(adjustment, sp_data_provider):
    """
    Test volume and prices output. Test description:
    - both adjustment and lack of adjustment is tested (no corporate actions exist for this ticker but it should
    not affect the result)
    - prices and volume are fetched for USD (currency attached to this ticker is JPY)
    """

    sp_data_provider.use_adjusted_prices = adjustment

    # Fetch prices in USD (exchange rate should be applied) and volume (no exchange rate should be applied)
    prices = sp_data_provider.get_history(SPTicker(2001), [SPField.ClosePrice, SPField.Volume], datetime(2011, 1, 1),
                                          datetime(2011, 1, 10), to_usd=True)
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_prices = QFDataFrame({
        SPField.ClosePrice: [20.0 / 150, 21.0 / 151, 22.0 / 153, 23.0 / 152],
        SPField.Volume: [100.0, None, 300.0, 400.0]
    }, index)
    expected_prices.name = "2001"
    expected_prices.columns.name = "fields"
    assert_dataframes_equal(prices, expected_prices)
