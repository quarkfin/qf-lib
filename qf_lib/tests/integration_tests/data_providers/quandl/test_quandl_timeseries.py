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

import unittest

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()


@unittest.skipIf(
    not hasattr(settings, "quandl_key"),
    "`quandl_key` property was not found in the settings.\n"
    "Set it using `QUANTFIN_SECRET` environment variable. Sample value of the env. variable: \n"
    "{\"quandl_key\": \"zW14dr45trz4up4d4juZ\"}\n"
    "To get the key, register an account at https://www.quandl.com"
)
class TestQuandlTimeseries(unittest.TestCase):
    START_DATE = str_to_date('2014-01-01')
    END_DATE = str_to_date('2015-02-02')

    SINGLE_TICKER = QuandlTicker('PKOBP', 'WSE')
    SINGLE_FIELD = 'Close'
    MANY_FIELDS = ['Close', 'High', 'Low']
    WSE_NUM_OF_DATES = 270
    WSE_OUTPUT_FIELDS = ['Open', 'High', 'Low', 'Close', '%Change', 'Volume', '# of Trades', 'Turnover (1000)']

    INVALID_TICKER = QuandlTicker('Inv1', 'WIKI')
    INVALID_TICKERS = [QuandlTicker('Inv1', 'WSE'), QuandlTicker('PKOBP', 'WSE'), QuandlTicker('MSFT', 'WSE')]

    MANY_TICKERS = [QuandlTicker('MSFT', 'WIKI'),
                    QuandlTicker('AAPL', 'WIKI'),
                    QuandlTicker('EA', 'WIKI'),
                    QuandlTicker('IBM', 'WIKI')]

    MIXED_DB_TICKERS = MANY_TICKERS + [QuandlTicker('IBM', 'WIKI/PRICES', QuandlDBType.Table),
                                       QuandlTicker('PKOBP', 'WSE')]

    WIKI_NUM_OF_DATES = 273
    WIKI_OUTPUT_FIELDS = ['Open', 'High', 'Low', 'Close', 'Volume', 'Ex-Dividend', 'Split Ratio', 'Adj. Open',
                          'Adj. High', 'Adj. Low', 'Adj. Close', 'Adj. Volume']
    MANY_TICKERS_STR = [t.as_string() for t in MANY_TICKERS]

    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    def setUp(self):
        self.quandl_provider = QuandlDataProvider(settings)

    # =========================== Test invalid ticker ==========================================================

    def test_price_single_invalid_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_price(tickers=self.INVALID_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), 0)
        self.assertEqual(data.name, self.INVALID_TICKER.as_string())

    def test_historical_single_invalid_ticker_no_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_history(tickers=self.INVALID_TICKER,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, QFDataFrame)
        self.assertEqual(len(data), 0)

    def test_price_single_invalid_ticker_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_price(tickers=self.INVALID_TICKER, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesDataFrame)
        self.assertEqual(data.shape, (0, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_single_invalid_ticker_all_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_history(tickers=self.INVALID_TICKER,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, QFDataFrame)
        self.assertEqual(data.shape, (0, 1))

    def test_price_many_invalid_tickers_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_price(tickers=self.INVALID_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.WSE_NUM_OF_DATES, len(self.INVALID_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.INVALID_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)

    # =========================== Test get_price method ==========================================================

    def test_price_single_ticker_single_field(self):
        data = self.quandl_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(len(data), self.WSE_NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_single_ticker_multiple_fields(self):
        data = self.quandl_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.WSE_NUM_OF_DATES, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_multiple_tickers_single_field(self):
        data = self.quandl_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertEqual(PricesDataFrame, type(data))
        self.assertEqual((self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS)), data.shape)
        self.assertEqual(self.MANY_TICKERS, list(data.columns))

    def test_price_multiple_tickers_multiple_fields(self):
        # testing for single date (start_date and end_date are the same)
        data = self.quandl_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)

    def test_price_mixed_databases(self):
        data = self.quandl_provider.get_price(tickers=self.MIXED_DB_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=Frequency.DAILY)
        self.assertEqual(type(data), QFDataArray)
        exected_number_of_dates = 280
        self.assertEqual(data.shape, (exected_number_of_dates, len(self.MIXED_DB_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MIXED_DB_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)

    # =========================== Test get_history method ==========================================================

    # ======================== Test Single Ticker
    def test_historical_single_ticker_no_field(self):
        # get all fields
        data = self.quandl_provider.get_history(tickers=self.SINGLE_TICKER,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, QFDataFrame)
        self.assertEqual(data.shape, (self.WSE_NUM_OF_DATES, len(self.WSE_OUTPUT_FIELDS)))
        self.assertEqual(set(data.columns), set(self.WSE_OUTPUT_FIELDS))

    def test_historical_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.SINGLE_FIELD,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, QFSeries)
        self.assertEqual(len(data), self.WSE_NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_historical_single_ticker_multiple_fields(self):
        data = self.quandl_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.MANY_FIELDS,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.WSE_NUM_OF_DATES, len(self.MANY_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_single_ticker_no_end_date(self):
        # get all fields
        data = self.quandl_provider.get_history(tickers=self.SINGLE_TICKER, start_date=self.START_DATE)

        self.assertIsInstance(data, QFDataFrame)
        self.assertTrue(data.shape[0] > self.WSE_NUM_OF_DATES)
        self.assertEqual(data.shape[1], len(self.WSE_OUTPUT_FIELDS))
        self.assertEqual(set(data.columns), set(self.WSE_OUTPUT_FIELDS))

    def test_historical_single_ticker_no_dates(self):
        # get all fields
        data = self.quandl_provider.get_history(tickers=self.SINGLE_TICKER)

        self.assertIsInstance(data, QFDataFrame)
        self.assertTrue(data.shape[0] > self.WSE_NUM_OF_DATES)
        self.assertEqual(data.shape[1], len(self.WSE_OUTPUT_FIELDS))
        self.assertEqual(set(data.columns), set(self.WSE_OUTPUT_FIELDS))

    # ======================== Test Multiple Tickers

    def test_historical_multiple_tickers_no_field(self):
        data = self.quandl_provider.get_history(tickers=self.MANY_TICKERS,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS), len(self.WIKI_OUTPUT_FIELDS)))
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(set(data.fields.values), set(self.WIKI_OUTPUT_FIELDS))

    def test_historical_multiple_tickers_single_field(self):
        data = self.quandl_provider.get_history(tickers=self.MANY_TICKERS, fields=self.SINGLE_FIELD,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_multiple_tickers_multiple_fields(self):
        data = self.quandl_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_FIELDS)


if __name__ == '__main__':
    unittest.main()
