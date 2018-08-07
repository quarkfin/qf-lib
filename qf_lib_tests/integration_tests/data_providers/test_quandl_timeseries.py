import unittest

import pandas as pd
from os.path import join

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings


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
    WIKI_NUM_OF_DATES = 273
    WIKI_OUTPUT_FIELDS = ['Open', 'High', 'Low', 'Close', 'Volume', 'Ex-Dividend', 'Split Ratio', 'Adj. Open',
                          'Adj. High', 'Adj. Low', 'Adj. Close', 'Adj. Volume']
    MANY_TICKERS_STR = [t.as_string() for t in MANY_TICKERS]

    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    def setUp(self):
        settings = Settings(join(get_src_root(), 'qf_lib_tests', 'unit_tests', 'config', 'test_settings.json'))
        self.quandl_provider = QuandlDataProvider(settings)

    # =========================== Test invalid ticker ==========================================================

    def test_price_single_invalid_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_price(tickers=self.INVALID_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), 0)
        self.assertEqual(data.name, self.INVALID_TICKER.as_string())

    def test_price_single_invalid_ticker_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.quandl_provider.get_price(tickers=self.INVALID_TICKER, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE)

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
                                              start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.WSE_NUM_OF_DATES, len(self.INVALID_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.items, pd.DatetimeIndex)
        self.assertEqual(list(data.major_axis), self.INVALID_TICKERS)
        self.assertEqual(list(data.minor_axis), self.MANY_PRICE_FIELDS)

    # =========================== Test get_price method ==========================================================

    def test_price_single_ticker_single_field(self):
        data = self.quandl_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), PricesSeries)
        self.assertEqual(len(data), self.WSE_NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_single_ticker_multiple_fields(self):
        data = self.quandl_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.WSE_NUM_OF_DATES, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_multiple_tickers_single_field(self):
        data = self.quandl_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_price_multiple_tickers_multiple_fields(self):
        # testing for single date (start_date and end_date are the same)
        data = self.quandl_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.items, pd.DatetimeIndex)
        self.assertEqual(list(data.major_axis), self.MANY_TICKERS)
        self.assertEqual(list(data.minor_axis), self.MANY_PRICE_FIELDS)

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

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS), len(self.WIKI_OUTPUT_FIELDS)))
        self.assertEqual(list(data.major_axis), self.MANY_TICKERS)
        self.assertEqual(set(data.minor_axis), set(self.WIKI_OUTPUT_FIELDS))

    def test_historical_multiple_tickers_single_field(self):
        data = self.quandl_provider.get_history(tickers=self.MANY_TICKERS, fields=self.SINGLE_FIELD,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_multiple_tickers_multiple_fields(self):
        data = self.quandl_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                                start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.WIKI_NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertEqual(list(data.major_axis), self.MANY_TICKERS)
        self.assertEqual(list(data.minor_axis), self.MANY_FIELDS)


if __name__ == '__main__':
    unittest.main()
