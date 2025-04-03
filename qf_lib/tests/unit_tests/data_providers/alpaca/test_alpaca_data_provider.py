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
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import patch, Mock, MagicMock

from pandas import Timestamp, DataFrame

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import AlpacaTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.data_providers.alpaca_py.alpaca_data_provider import AlpacaDataProvider

try:
    from alpaca.data import StockHistoricalDataClient, StockBarsRequest, TimeFrame, CryptoHistoricalDataClient, \
        CryptoBarsRequest

    is_alpaca_intalled = True
except ImportError:
    is_alpaca_intalled = False


class TestAlpacaDataProvider(TestCase):

    def _mock_daily_data(self, request, **kwargs):
        mocked_data = {'close': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1834.349,
                                 ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1823.4},
                       'high': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1955.299,
                                ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1840.095},
                       'low': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1781.48,
                               ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1806.4825},
                       'open': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1878.96,
                                ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1835.575},
                       'trade_count': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 137.0,
                                       ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 9.0},
                       'volume': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 50.873426536,
                                  ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 30.698688015},
                       'vwap': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1839.6209146235,
                                ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1817.2097161756}}
        df = DataFrame.from_dict(mocked_data)
        start = (request.start + RelativeDelta(hour=5, minute=0)).replace(tzinfo=timezone.utc)
        end = (request.end + RelativeDelta(hour=5, minute=0)).replace(tzinfo=timezone.utc)
        df = df.reset_index().rename(columns={'level_0': 'symbol', 'level_1': 'timestamp'})
        df = df[df['symbol'].isin(request.symbol_or_symbols)]
        df = df.set_index('timestamp').loc[start:end].reset_index()
        df = df.set_index(['symbol', 'timestamp'])
        return Mock(df=df)

    @patch('qf_lib.data_providers.alpaca_py.alpaca_data_provider.CryptoHistoricalDataClient')
    def test_get_history__single_ticker_single_date_single_field(self, crypto_mock):
        mocked = MagicMock()
        mocked.get_crypto_bars.side_effect = self._mock_daily_data
        crypto_mock.return_value = mocked

        data_provider = AlpacaDataProvider()
        close_price = data_provider.get_history(AlpacaTicker("ABC/USD", SecurityType.CRYPTO), "close",
                                       datetime(2021, 1, 3),  datetime(2021, 1, 3))
        self.assertEqual(close_price, 1823.4)