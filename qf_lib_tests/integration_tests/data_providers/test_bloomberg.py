import unittest

import pandas as pd
from os.path import join

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings
from qf_lib.testing_tools.containers_comparison import assert_series_equal

settings = Settings(join(get_src_root(), 'qf_lib_tests', 'unit_tests', 'config', 'test_settings.json'))
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestBloomberg(unittest.TestCase):
    START_DATE = str_to_date('2014-01-01')
    END_DATE = str_to_date('2015-02-02')
    SINGLE_FIELD = 'PX_LAST'
    MANY_FIELDS = ['PX_LAST', 'OPEN', 'HIGH']
    INVALID_TICKER = BloombergTicker('Inv TIC Equity')
    INVALID_TICKERS = [BloombergTicker('Inv1 TIC Equity'), BloombergTicker('AAPL US Equity'),
                       BloombergTicker('Inv2 TIC Equity')]

    SINGLE_TICKER = BloombergTicker('IBM US Equity')
    MANY_TICKERS = [BloombergTicker('IBM US Equity'), BloombergTicker('AAPL US Equity')]
    NUM_OF_DATES = 273
    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    def setUp(self):
        self.bbg_provider = bbg_provider

# =========================== Test invalid ticker ==========================================================

    def test_price_single_invalid_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.INVALID_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), 0)
        self.assertEqual(data.name, self.INVALID_TICKER.as_string())

    def test_price_single_invalid_ticker_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.INVALID_TICKER, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, PricesDataFrame)
        self.assertEqual(data.shape, (0, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_many_invalid_tickers_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.INVALID_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.INVALID_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.items, pd.DatetimeIndex)
        self.assertEqual(list(data.major_axis), self.INVALID_TICKERS)
        self.assertEqual(list(data.minor_axis), self.MANY_PRICE_FIELDS)

# =========================== Test get_price method ==========================================================

    def test_price_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_single_ticker_multiple_fields(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_multiple_tickers_single_field(self):
        data = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_price_multiple_tickers_single_field_order(self):
        data1 = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE)

        data2 = self.bbg_provider.get_price(tickers=[self.MANY_TICKERS[1], self.MANY_TICKERS[0]],
                                            fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE)

        assert_series_equal(data2.iloc[:, 0], data1.iloc[:, 1])
        assert_series_equal(data2.iloc[:, 1], data1.iloc[:, 0])

    def test_price_multiple_tickers_multiple_fields(self):
        # testing for single date (start_date and end_date are the same)
        data = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.items, pd.DatetimeIndex)
        self.assertEqual(list(data.major_axis), self.MANY_TICKERS)
        self.assertEqual(list(data.minor_axis), self.MANY_PRICE_FIELDS)

# =========================== Test get_history method ==========================================================

    def test_historical_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=Frequency.DAILY, currency='CHF')

        self.assertIsInstance(data, QFSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_historical_single_ticker_multiple_fields(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.MANY_FIELDS,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=Frequency.DAILY, currency='PLN')

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_multiple_tickers_single_field(self):
        data = self.bbg_provider.get_history(tickers=self.MANY_TICKERS, fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=Frequency.DAILY, currency='PLN')
        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_multiple_tickers_multiple_fields_one_date(self):
        # testing for single date (start_date and end_date are the same)
        data = self.bbg_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                             start_date=self.END_DATE, end_date=self.END_DATE,
                                             frequency=Frequency.DAILY, currency='PLN')
        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertEqual(list(data.index), self.MANY_TICKERS)
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_multiple_tickers_multiple_fields_many_dates(self):
        # testing for single date (start_date and end_date are the same)
        data = self.bbg_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=Frequency.DAILY, currency='PLN')
        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertIsInstance(data.items, pd.DatetimeIndex)
        self.assertEqual(list(data.major_axis), self.MANY_TICKERS)
        self.assertEqual(list(data.minor_axis), self.MANY_FIELDS)

    def test_historical_single_ticker_single_field_list1(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_history(tickers=[self.SINGLE_TICKER], fields=[self.SINGLE_FIELD],
                                                   start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, pd.Panel)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, 1, 1))

    def test_historical_single_ticker_single_field_list2(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.bbg_provider.get_history(tickers=[self.SINGLE_TICKER], fields=self.SINGLE_FIELD,
                                                   start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, 1))
        self.assertEqual(list(data.columns), [self.SINGLE_TICKER])

    def test_historical_single_ticker_single_field_list3(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=[self.SINGLE_FIELD],
                                                   start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, 1))
        self.assertEqual(list(data.columns), [self.SINGLE_FIELD])

    def test_historical_single_ticker_single_field_no_end_date(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE)
        self.assertTrue(len(data) >= self.NUM_OF_DATES)

# =========================== Test get_current_values method ==========================================================

    def test_current_many_tickers_many_fields(self):
        data = self.bbg_provider.get_current_values(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (len(self.MANY_TICKERS), len(self.MANY_FIELDS)))

        self.assertEqual(list(data.index), self.MANY_TICKERS)
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_current_many_tickers_one_field(self):
        data = self.bbg_provider.get_current_values(tickers=self.MANY_TICKERS, fields=self.SINGLE_FIELD)

        self.assertEqual(type(data), QFSeries)
        self.assertEqual(data.size, len(self.MANY_TICKERS))
        self.assertEqual(data.name, self.SINGLE_FIELD)
        self.assertEqual(list(data.index), self.MANY_TICKERS)

    def test_current_one_ticker_many_fields(self):
        data = self.bbg_provider.get_current_values(tickers=self.SINGLE_TICKER, fields=self.MANY_FIELDS)

        self.assertEqual(type(data), QFSeries)
        self.assertEqual(data.size, len(self.MANY_FIELDS))
        self.assertEqual(data.name, self.SINGLE_TICKER)
        self.assertEqual(list(data.index), self.MANY_FIELDS)

# =========================== Test override ==========================================================

    def test_override_historical_single_ticker_single_field(self):
        start_date = str_to_date('2015-10-31')
        end_date = str_to_date('2016-03-31')
        ticker = BloombergTicker('DGNOXTCH Index')
        data = self.bbg_provider.get_history(tickers=ticker, fields='ACTUAL_RELEASE',
                                             start_date=start_date, end_date=end_date)

        override_data = self.bbg_provider.get_history(tickers=ticker, fields='ACTUAL_RELEASE',
                                                      start_date=start_date, end_date=end_date,
                                                      override_name='RELEASE_STAGE_OVERRIDE', override_value='P')

        data_model = [0.5, 0, -1, 1.7, -1.3, -0.2]
        override_data_model = [0.5, -0.1, -1.2, 1.8, -1, -0.2]

        self.assertSequenceEqual(seq1=data_model, seq2=data.tolist())
        self.assertSequenceEqual(seq1=override_data_model, seq2=override_data.tolist())


if __name__ == '__main__':
    unittest.main()
