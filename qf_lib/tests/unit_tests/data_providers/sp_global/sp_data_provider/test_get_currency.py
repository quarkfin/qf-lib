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

import pytest

from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.series.qf_series import QFSeries


@pytest.mark.parametrize("tradingitemid,expected_currency", [(2001, "JPY"), (2002, None), (-17, None), (2003, "USD")])
def test_get_currency__single_ticker(tradingitemid, expected_currency, sp_data_provider):
    currency = sp_data_provider.get_currency(SPTicker(tradingitemid))
    assert currency == expected_currency


def test_get_currency__multiple_tickers(sp_data_provider):
    """ Test fetching currencies for more than 1000 tickers. """
    currencies = sp_data_provider.get_currency([SPTicker(i) for i in range(1, 1501)])
    assert len(currencies) == 1500
    assert isinstance(currencies, QFSeries)
