import unittest
from pandas import to_datetime
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_data_provider import BloombergBeapHapiDataProvider
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings
from strategies.cta_strategy.cta_tickers_universe import DAYS_BEFORE_EXP_DATE
from datetime import datetime


class TestBloombergBeapHapi(unittest.TestCase):

    START_DATE = str_to_date('2021-01-01')
    END_DATE = str_to_date('2021-07-01')
    SINGLE_FIELD = 'PX_LAST'
    MANY_FIELDS = ['PX_LAST', 'PX_OPEN', 'PX_HIGH']
    EXPIRATION_DATES = ExpirationDateField.all_dates()

    INVALID_INDEX = BloombergTicker('RTYADSM1 Index')
    INVALID_INDEXES = [BloombergTicker('ASDVCXZASD Index'), BloombergTicker('ASDBVCX ComSADFdty')]

    INVALID_FUTURE_INDEX = BloombergFutureTicker('E-mini Russell 2000 Inndex Futures', 'RTASY{} Index', 1, DAYS_BEFORE_EXP_DATE, 50, "HMUZ")
    INVALID_FUTURE_INDEXES = [BloombergFutureTicker('E-mini Russella 2000 Index Futures', 'RTASY{} Index', 1, DAYS_BEFORE_EXP_DATE, 50, "HMUZ"),
                              BloombergFutureTicker("Cotton", "CT{} Comddty", 1, 3)]

    SINGLE_INDEX = BloombergTicker('RTYM1 Index')
    MANY_INDEXES = [BloombergTicker('RTYM1 Index'), BloombergTicker('CTA Comdty')]

    SINGLE_FUTURE_INDEX = BloombergFutureTicker('E-mini Russell 2000 Index Futures', 'RTY{} Index', 1, DAYS_BEFORE_EXP_DATE, 50, "HMUZ")
    MANY_FUTURE_INDEXES = [BloombergFutureTicker('E-mini Russell 2000 Index Futures', 'RTY{} Index', 1, DAYS_BEFORE_EXP_DATE, 50, "HMUZ"),
                           BloombergFutureTicker("Cotton", "CT{} Comdty", 1, 3)]

    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    def setUp(self):

        settings = get_test_settings()

        # if there is no credentials or access to HAPI - integration tests are skipped
        try:
            self.bbg_beap_hapi = BloombergBeapHapiDataProvider(settings)
        except Exception as e:
            raise self.skipTest(e)

    # =========================== Tests ==========================================================

    def test_get_history_single_ticker_single_field(self):
        data = self.bbg_beap_hapi.get_history(self.SINGLE_INDEX, self.SINGLE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(type(data), QFSeries)
        self.assertEqual(self.SINGLE_INDEX.as_string(), data.name)
        self.assertTrue(data.index.min() >= self.START_DATE and data.index.max() <= self.END_DATE)

    def test_get_history_single_ticker_many_fields(self):
        data = self.bbg_beap_hapi.get_history(self.SINGLE_INDEX, self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(len(self.MANY_FIELDS), data.shape[1])
        self.assertTrue(data.index.min() >= self.START_DATE and data.index.max() <= self.END_DATE)

    def test_get_history_many_tickers_many_fields(self):
        data = self.bbg_beap_hapi.get_history(self.MANY_INDEXES, self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(len(self.MANY_INDEXES), len(data.tickers))
        self.assertEqual(len(self.MANY_FIELDS), len(data.fields))
        self.assertTrue(to_datetime(data.dates.values.min()) >= self.START_DATE and to_datetime(data.dates.values.max()) <= self.END_DATE)

    def test_get_futures_chain_tickers_single_ticker_expiration_dates(self):
        data = self.bbg_beap_hapi.get_futures_chain_tickers(self.SINGLE_FUTURE_INDEX, self.EXPIRATION_DATES)

        self.assertTrue(type(data), dict)
        self.assertTrue(len(data), 1)
        self.assertTrue(type(data[list(data.keys())[0]]), QFDataFrame)
        self.assertTrue(list(data.keys()) == [self.SINGLE_FUTURE_INDEX])

    def test_get_futures_chain_tickers_many_tickers_expiration_dates(self):
        data = self.bbg_beap_hapi.get_futures_chain_tickers(self.MANY_FUTURE_INDEXES, self.EXPIRATION_DATES)

        self.assertEqual(type(data), dict)
        self.assertEqual(len(data), 2)
        self.assertTrue(type(data[list(data.keys())[0]]), QFDataFrame)
        self.assertTrue(list(data.keys()) == self.MANY_FUTURE_INDEXES)
        self.assertCountEqual(data[list(data.keys())[0]].columns.values, self.EXPIRATION_DATES)

    def test_get_history_invalid_ticker_single_field(self):
        data = self.bbg_beap_hapi.get_history(self.INVALID_INDEX, self.SINGLE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(QFSeries, type(data))
        self.assertTrue(data.empty)
        self.assertEqual(self.INVALID_INDEX.as_string(), data.name)

    def test_get_history_invalid_ticker_many_fields(self):
        data = self.bbg_beap_hapi.get_history(self.INVALID_INDEX, self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataFrame, type(data))
        self.assertTrue(data.empty)
        self.assertCountEqual(self.MANY_FIELDS, data.columns.values)

    def test_get_history_invalid_many_tickers_single_field(self):
        data = self.bbg_beap_hapi.get_history(self.INVALID_INDEXES, self.SINGLE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataFrame, type(data))
        self.assertTrue(data.empty)
        self.assertCountEqual(self.INVALID_INDEXES, data.columns.values)

    def test_get_history_invalid_many_tickers_many_fields(self):
        data = self.bbg_beap_hapi.get_history(self.INVALID_INDEXES, self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataArray, type(data))
        self.assertCountEqual(self.MANY_FIELDS, data.fields.values)
        self.assertCountEqual(self.INVALID_INDEXES, data.tickers.values)

    def test_get_history_invalid_and_correct_ticker_single_field(self):
        data = self.bbg_beap_hapi.get_history([self.SINGLE_INDEX] + [self.INVALID_INDEX], self.SINGLE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataFrame, type(data))
        self.assertFalse(data.empty)
        self.assertCountEqual([self.SINGLE_INDEX] + [self.INVALID_INDEX], data.columns.values)
        self.assertTrue(data.index.min() >= self.START_DATE and data.index.max() <= self.END_DATE)
        self.assertTrue(data[self.INVALID_INDEX].isnull().all())

    def test_get_history_invalid_and_correct_ticker_many_fields(self):
        data = self.bbg_beap_hapi.get_history([self.SINGLE_INDEX] + [self.INVALID_INDEX], self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataArray, type(data))
        self.assertCountEqual(self.MANY_FIELDS, data.fields.values)
        self.assertCountEqual([self.SINGLE_INDEX] + [self.INVALID_INDEX], data.tickers.values)
        self.assertTrue(to_datetime(data.dates.values.min()) >= self.START_DATE and to_datetime(data.dates.values.max()) <= self.END_DATE)

    def test_get_history_invalid_and_correct_tickers_single_fields(self):
        data = self.bbg_beap_hapi.get_history(self.MANY_INDEXES + self.INVALID_INDEXES, self.SINGLE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataFrame, type(data))
        self.assertFalse(data.empty)
        self.assertCountEqual(self.MANY_INDEXES + self.INVALID_INDEXES, data.columns.values)
        self.assertTrue(data.index.min() >= self.START_DATE and data.index.max() <= self.END_DATE)

    def test_get_history_invalid_and_correct_tickers_many_fields(self):
        data = self.bbg_beap_hapi.get_history(self.MANY_INDEXES + self.INVALID_INDEXES, self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataArray, type(data))
        self.assertCountEqual(self.MANY_INDEXES + self.INVALID_INDEXES, data.tickers.values)
        self.assertCountEqual(self.MANY_FIELDS, data.fields.values)
        self.assertTrue(to_datetime(data.dates.values.min()) >= self.START_DATE and to_datetime(data.dates.values.max()) <= self.END_DATE)

    def test_get_futures_chain_tickers_invalid_ticker(self):
        self.assertRaises(BloombergError, self.bbg_beap_hapi.get_futures_chain_tickers, self.INVALID_FUTURE_INDEX, self.EXPIRATION_DATES)

    def test_get_futures_chain_tickers_invalid_tickers(self):
        self.assertRaises(BloombergError, self.bbg_beap_hapi.get_futures_chain_tickers, self.INVALID_FUTURE_INDEXES, self.EXPIRATION_DATES)

    def test_get_futures_chain_tickers_correct_and_invalid_ticker(self):
        data = self.bbg_beap_hapi.get_futures_chain_tickers([self.SINGLE_FUTURE_INDEX] + [self.INVALID_FUTURE_INDEX], self.EXPIRATION_DATES)

        self.assertEqual(dict, type(data))
        self.assertEqual(len(data.keys()), 2)
        self.assertEqual(type(data[list(data.keys())[0]]), QFDataFrame)
        self.assertCountEqual(data[list(data.keys())[0]].columns.values, self.EXPIRATION_DATES)

    def test_get_futures_chain_tickers_correct_and_invalid_tickers(self):
        data = self.bbg_beap_hapi.get_futures_chain_tickers(self.MANY_FUTURE_INDEXES + self.INVALID_FUTURE_INDEXES, self.EXPIRATION_DATES)

        self.assertEqual(dict, type(data))
        self.assertEqual(len(data.keys()), len(self.MANY_FUTURE_INDEXES + self.INVALID_FUTURE_INDEXES))
        self.assertEqual(type(data[list(data.keys())[0]]), QFDataFrame)
        self.assertCountEqual(data[list(data.keys())[0]].columns.values, self.EXPIRATION_DATES)

    def test_get_price_single_ticker_single_price_field(self):
        data = self.bbg_beap_hapi.get_price(self.SINGLE_INDEX, self.SINGLE_PRICE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(PricesSeries, type(data))
        self.assertEqual(self.SINGLE_INDEX.as_string(), data.name)
        self.assertTrue(to_datetime(data.index.values.min()) >= self.START_DATE and to_datetime(data.index.values.max()) <= self.END_DATE)

    def test_get_price_single_ticker_many_price_fields(self):
        data = self.bbg_beap_hapi.get_price(self.SINGLE_INDEX, self.MANY_PRICE_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(PricesDataFrame, type(data))
        self.assertCountEqual(self.MANY_PRICE_FIELDS, data.columns.values)
        self.assertTrue(to_datetime(data.index.values.min()) >= self.START_DATE and to_datetime(data.index.values.max()) <= self.END_DATE)

    def test_get_price_invalid_and_correct_ticker_single_fields(self):
        data = self.bbg_beap_hapi.get_price([self.SINGLE_INDEX]+[self.INVALID_INDEX], self.SINGLE_PRICE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(PricesDataFrame, type(data))
        self.assertCountEqual([self.SINGLE_INDEX]+[self.INVALID_INDEX], data.columns.values)
        self.assertTrue(to_datetime(data.index.values.min()) >= self.START_DATE and to_datetime(data.index.values.max()) <= self.END_DATE)

    def test_get_price_invalid_and_correct_tickers_many_fields(self):
        data = self.bbg_beap_hapi.get_price(self.MANY_INDEXES+self.INVALID_INDEXES, self.MANY_PRICE_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataArray, type(data))
        self.assertCountEqual(self.MANY_INDEXES + self.INVALID_INDEXES, data.tickers.values)
        self.assertCountEqual(self.MANY_PRICE_FIELDS, data.fields.values)
        self.assertTrue(to_datetime(data.dates.values.min()) >= self.START_DATE and to_datetime(data.dates.values.max()) <= self.END_DATE)

    def test_get_history_correct_single_future_ticker_single_field(self):
        self.SINGLE_FUTURE_INDEX.initialize_data_provider(SettableTimer(datetime.now()), self.bbg_beap_hapi)
        data = self.bbg_beap_hapi.get_history(self.SINGLE_FUTURE_INDEX, self.SINGLE_FIELD, self.START_DATE, self.END_DATE)

        self.assertEqual(QFSeries, type(data))
        self.assertTrue(data.index.min() >= self.START_DATE and data.index.max() <= self.END_DATE)

    def test_get_history_correct_single_future_ticker_many_tickers_many_fields(self):
        self.SINGLE_FUTURE_INDEX.initialize_data_provider(SettableTimer(datetime.now()), self.bbg_beap_hapi)
        data = self.bbg_beap_hapi.get_history([self.SINGLE_FUTURE_INDEX] + self.MANY_INDEXES, self.MANY_FIELDS, self.START_DATE, self.END_DATE)

        self.assertEqual(QFDataArray, type(data))
        self.assertCountEqual(self.MANY_FIELDS, data.fields.values)
        self.assertTrue(to_datetime(data.dates.values.min()) >= self.START_DATE and to_datetime(data.dates.values.max()) <= self.END_DATE)


if __name__ == '__main__':
    unittest.main()
