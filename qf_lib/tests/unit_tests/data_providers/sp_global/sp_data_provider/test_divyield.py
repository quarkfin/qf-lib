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

from pandas import DatetimeIndex

from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.sp_global.sp_field import SPField
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


def test_when_tid_currency_matches_dividend_currency(sp_data_provider):
    """
    - currency of the tradingitem is USD
    - currency of all the dividend yield values is USD
    - the enddate of the divyield is NOT inclusive
    """
    divyield = sp_data_provider.get_history(SPTicker(2003), SPField.DivYield, datetime(2011, 1, 1),
                                            datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_divyield = QFSeries([10 / 20, 10 / 21, 50 / 22, 50 / 23], index, name="2003") * 100
    assert_series_equal(divyield, expected_divyield)


def test_when_tid_has_no_currency_attached(sp_data_provider):
    """
    - currency of the tradingitem is None
    """
    divyield = sp_data_provider.get_history(SPTicker(2002), SPField.DivYield, datetime(2011, 1, 1),
                                            datetime(2011, 1, 5))
    assert divyield.empty


def test_when_tid_currency_does_not_match_dividend_currency(sp_data_provider):
    """
    - currency of the tradingitem is JPY
    - currency of all the dividend yield values is USD
    """
    divyield = sp_data_provider.get_history(SPTicker(2001), SPField.DivYield, datetime(2011, 1, 1),
                                            datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_divyield = QFSeries([10 / (20 / 150), 10 / (21 / 151), 50 / (22 / 153), 50 / (23 / 152)],
                                 index, name="2001") * 100
    assert_series_equal(divyield, expected_divyield)


def test_when_tid_currency_does_not_match_dividend_currency_2(sp_data_provider):
    """
    - currency of the tradingitem is USD
    - currency of all the dividend yield values is JPY
    """
    divyield = sp_data_provider.get_history(SPTicker(2004), SPField.DivYield, datetime(2011, 1, 1),
                                            datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_divyield = QFSeries([10 / (20 * 150), 10 / (21 * 151), 50 / (22 * 153), 50 / (23 * 152)],
                                 index, name="2004") * 100
    assert_series_equal(divyield, expected_divyield)


def test_gaps_in_divyield(sp_data_provider):
    """
    - currency of the tradingitem is USD
    - currency of all the dividend yield values is JPY
    """
    divyield = sp_data_provider.get_history(SPTicker(2005), SPField.DivYield, datetime(2011, 1, 1),
                                            datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-04', '2011-01-05'], name="dates")
    expected_divyield = QFSeries([10 / (20 * 150), 50 / (22 * 153), 50 / (23 * 152)],
                                 index, name="2005") * 100
    assert_series_equal(divyield, expected_divyield)


def test_divyield_multiple_currencies(sp_data_provider):
    """
    - currency of the tradingitem is USD
    - currency of some dividend yields is USD (first two days), some JPY
    """
    divyield = sp_data_provider.get_history(SPTicker(2006), SPField.DivYield, datetime(2011, 1, 1),
                                            datetime(2011, 1, 5))
    index = DatetimeIndex(['2011-01-01', '2011-01-02', '2011-01-04', '2011-01-05'], name="dates")
    expected_divyield = QFSeries([10 / 20, 10 / 21, 50 / (22 * 153), 50 / (23 * 152)],
                                 index, name="2006") * 100
    assert_series_equal(divyield, expected_divyield)
