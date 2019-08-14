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

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import CcyTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.cryptocurrency.cryptocurrency_data_provider import CryptoCurrencyDataProvider


@unittest.skip("CryptoCurrencyDataProvider needs update")
class TestCryptoCurrency(unittest.TestCase):
    START_DATE = str_to_date('2016-01-01')
    END_DATE = str_to_date('2017-02-02')
    SINGLE_FIELD = 'Close'
    MANY_FIELDS = ['Open', 'Volume', 'Close']

    SINGLE_TICKER = CcyTicker('Bitcoin')
    MANY_TICKERS = [CcyTicker('Bitcoin'), CcyTicker('Ethereum'), CcyTicker('Ripple')]
    NUM_OF_DATES = 399

    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    def setUp(self):
        self.cryptocurrency_provider = CryptoCurrencyDataProvider()

    # =========================== Test get_price method ==========================================================

    def test_price_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.cryptocurrency_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                                      start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_single_ticker_multiple_fields(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.cryptocurrency_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.MANY_PRICE_FIELDS,
                                                      start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_multiple_tickers_single_field(self):
        data = self.cryptocurrency_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                                      start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_price_multiple_tickers_multiple_fields(self):
        # testing for single date (start_date and end_date are the same)
        data = self.cryptocurrency_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                                      start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)

    # =========================== Test get_history method ==========================================================

    def test_historical_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.cryptocurrency_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.SINGLE_FIELD,
                                                        start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, QFSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_historical_single_ticker_multiple_fields(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.cryptocurrency_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.MANY_FIELDS,
                                                        start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_multiple_tickers_single_field(self):
        data = self.cryptocurrency_provider.get_history(tickers=self.MANY_TICKERS, fields=self.SINGLE_FIELD,
                                                        start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_multiple_tickers_multiple_fields_one_date(self):
        # testing for single date (start_date and end_date are the same)
        data = self.cryptocurrency_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                                        start_date=self.END_DATE, end_date=self.END_DATE)
        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertEqual(list(data.index), self.MANY_TICKERS)
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_multiple_tickers_multiple_fields_many_dates(self):
        # testing for single date (start_date and end_date are the same)
        data = self.cryptocurrency_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                                        start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_FIELDS)


if __name__ == '__main__':
    unittest.main()
