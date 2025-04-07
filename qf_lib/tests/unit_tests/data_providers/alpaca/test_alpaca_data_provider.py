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
from unittest.mock import patch, Mock

import pytest
from numpy import nan
from pandas import Timestamp, DataFrame, isnull
from statsmodels.compat.pandas import assert_frame_equal

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import AlpacaTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.alpaca_py.alpaca_data_provider import AlpacaDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataarrays_equal

try:
    from alpaca.data import CryptoHistoricalDataClient

    is_alpaca_installed = True
except ImportError:
    is_alpaca_installed = False


@pytest.mark.skipif(not is_alpaca_installed, reason="requires alpaca")
class TestAlpacaDataProvider(TestCase):

    def setUp(self):
        self.patcher = patch.object(CryptoHistoricalDataClient, 'get_crypto_bars', side_effect=self._mock_daily_data)
        self.patcher.start()
        self.data_provider = AlpacaDataProvider()

    def tearDown(self):
        self.patcher.stop()

    def test_supported_tickers(self):
        self.assertCountEqual(self.data_provider.supported_ticker_types(), {AlpacaTicker})

    """ Test get_history """

    def test_get_history__single_ticker_single_date_single_field(self):
        close_price = self.data_provider.get_history(AlpacaTicker("ABC/USD", SecurityType.CRYPTO), "close",
                                                     datetime(2021, 1, 3), datetime(2021, 1, 3))
        self.assertEqual(close_price, 1823.4)

    def test_get_history__single_ticker_single_date_multiple_fields(self):
        prices_series = self.data_provider.get_history(AlpacaTicker("ABC/USD", SecurityType.CRYPTO), ["close", "open"],
                                                       datetime(2021, 1, 3), datetime(2021, 1, 3))
        expected_series = QFSeries(name="ABC/USD", data=[1823.4, 1835.575], index=["close", "open"])
        expected_series.index.name = "fields"
        assert_series_equal(expected_series, prices_series)

    def test_get_history__single_ticker_single_date_multiple_fields_2(self):
        prices_series = self.data_provider.get_history(AlpacaTicker("ABC/USD", SecurityType.CRYPTO), ["close"],
                                                       datetime(2021, 1, 3), datetime(2021, 1, 3))
        expected_series = QFSeries(name="ABC/USD", data=[1823.4], index=["close"])
        expected_series.index.name = "fields"
        assert_series_equal(expected_series, prices_series)

    def test_get_history__single_ticker_multiple_dates_multiple_fields(self):
        prices_df = self.data_provider.get_history(AlpacaTicker("ABC/USD", SecurityType.CRYPTO), ["close", "open"],
                                                   datetime(2021, 1, 2), datetime(2021, 1, 3))
        expected_df = QFDataFrame(data={"close": [1834.349, 1823.4], "open": [1878.96, 1835.575]},
                                  index=[datetime(2021, 1, 2), datetime(2021, 1, 3)], columns=["close", "open"])
        expected_df.name = "ABC/USD"
        expected_df.index.name = "dates"
        expected_df.columns.name = "fields"
        assert_frame_equal(expected_df, prices_df)

    def test_get_history__single_ticker_multiple_dates_single_field(self):
        prices_series = self.data_provider.get_history(AlpacaTicker("ABC/USD", SecurityType.CRYPTO), "close",
                                                       datetime(2021, 1, 2), datetime(2021, 1, 3))
        expected_series = QFSeries(data=[1834.349, 1823.4],
                                   index=[datetime(2021, 1, 2), datetime(2021, 1, 3)])
        expected_series.name = "ABC/USD"
        expected_series.index.name = "dates"
        assert_series_equal(expected_series, prices_series)

    def test_get_history__incorrect_ticker(self):
        empty = self.data_provider.get_history(AlpacaTicker("Incorrect", SecurityType.CRYPTO), "close",
                                               datetime(2021, 1, 3), datetime(2021, 1, 3))
        self.assertTrue(isnull(empty))

    def test_get_history__multiple_tickers_single_date_single_field(self):
        prices_series = self.data_provider.get_history(
            [AlpacaTicker("ABC/USD", SecurityType.CRYPTO), AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)],
            "close", datetime(2021, 1, 3), datetime(2021, 1, 3))
        expected_series = QFSeries(name="close", data=[1823.4, 1840.095],
                                   index=[AlpacaTicker("ABC/USD", SecurityType.CRYPTO),
                                          AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)])
        expected_series.index.name = "tickers"
        assert_series_equal(expected_series, prices_series)

    def test_get_history__multiple_tickers_single_date_multiple_fields(self):
        prices_df = self.data_provider.get_history(
            [AlpacaTicker("ABC/USD", SecurityType.CRYPTO), AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)],
            ["close", "open"], datetime(2021, 1, 3), datetime(2021, 1, 3))
        expected_df = QFDataFrame(data={"close": [1823.4, 1840.095], "open": [1835.575, nan]},
                                  index=[AlpacaTicker("ABC/USD", SecurityType.CRYPTO),
                                         AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)], columns=["close", "open"])
        expected_df.index.name = "tickers"
        expected_df.columns.name = "fields"
        assert_frame_equal(expected_df, prices_df)

    def test_get_history__multiple_tickers_multiple_dates_single_field(self):
        prices_df = self.data_provider.get_history(
            [AlpacaTicker("ABC/USD", SecurityType.CRYPTO), AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)],
            "close", datetime(2021, 1, 2), datetime(2021, 1, 3))
        expected_df = QFDataFrame(data={AlpacaTicker("ABC/USD", SecurityType.CRYPTO): [1834.349, 1823.4],
                                        AlpacaTicker("XYZ/USD", SecurityType.CRYPTO): [1955.299, 1840.095]},
                                  index=[datetime(2021, 1, 2), datetime(2021, 1, 3)],
                                  columns=[AlpacaTicker("ABC/USD", SecurityType.CRYPTO),
                                           AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)])
        expected_df.index.name = "dates"
        expected_df.columns.name = "tickers"
        assert_frame_equal(expected_df, prices_df)

    def test_get_history__multiple_tickers_multiple_dates_multiple_fields(self):
        prices = self.data_provider.get_history(
            [AlpacaTicker("ABC/USD", SecurityType.CRYPTO), AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)],
            ["close", "open"], datetime(2021, 1, 2), datetime(2021, 1, 3))

        expected = QFDataArray.create([datetime(2021, 1, 2), datetime(2021, 1, 3)],
                                      [AlpacaTicker("ABC/USD", SecurityType.CRYPTO),
                                       AlpacaTicker("XYZ/USD", SecurityType.CRYPTO)],
                                      ["close", "open"],
                                      data=[[
                                          [1834.349, 1878.96],
                                          [1955.299, nan]
                                      ], [
                                          [1823.4, 1835.575],
                                          [1840.095, nan]
                                      ]])
        assert_dataarrays_equal(prices, expected)

    @staticmethod
    def _mock_daily_data(request, **kwargs):
        """ Mock the daily data request to ensure the output is the same as the output of the alpaca historical
        request."""

        mocked_data = {'close': {('ABC/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1834.349,
                                 ('ABC/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1823.4,
                                 ('XYZ/USD', Timestamp('2021-01-02 05:00:00+0000', tz='UTC')): 1955.299,
                                 ('XYZ/USD', Timestamp('2021-01-03 05:00:00+0000', tz='UTC')): 1840.095
                                 },
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
        df = df[df['timestamp'] >= start]
        df = df[df['timestamp'] <= end]
        df = df.set_index(['symbol', 'timestamp'])

        if df.empty:
            df = DataFrame()

        return Mock(df=df)
