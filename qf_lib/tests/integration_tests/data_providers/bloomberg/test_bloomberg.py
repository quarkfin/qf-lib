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

import numpy as np
import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal
from qf_lib.tests.integration_tests.connect_to_data_provider import get_data_provider


class TestBloomberg(unittest.TestCase):
    START_DATE = str_to_date('2014-01-01')
    END_DATE = str_to_date('2015-02-02')
    SINGLE_FIELD = 'PX_LAST'
    MANY_FIELDS = ['PX_LAST', 'PX_OPEN', 'PX_HIGH']
    INVALID_TICKER = BloombergTicker('Inv TIC Equity')
    INVALID_TICKERS = [BloombergTicker('Inv1 TIC Equity'), BloombergTicker('AAPL US Equity'),
                       BloombergTicker('Inv2 TIC Equity')]

    SINGLE_TICKER = BloombergTicker('IBM US Equity')
    MANY_TICKERS = [BloombergTicker('IBM US Equity'), BloombergTicker('AAPL US Equity')]
    NUM_OF_DATES = 273
    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    def setUp(self):
        try:
            self.bbg_provider = get_data_provider()
        except Exception as e:
            raise self.skipTest(e)

    # =========================== Test invalid ticker ==========================================================

    def test_price_single_invalid_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.INVALID_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), 0)
        self.assertEqual(data.name, self.INVALID_TICKER.as_string())

    def test_price_single_invalid_ticker_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.INVALID_TICKER, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesDataFrame)
        self.assertEqual(data.shape, (0, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_many_invalid_tickers_many_fields(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.INVALID_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.INVALID_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.INVALID_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)

    # =========================== Test get_price method ==========================================================

    def test_price_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_single_ticker_single_field_single_date(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.END_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertIsInstance(data, float)
        self.assertEqual(data, 147.7257)

    def test_price_single_ticker_multiple_fields(self):
        # single ticker, many fields; can be the same as for single field???
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_multiple_tickers_single_field(self):
        data = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)
        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_price_multiple_tickers_single_field_order(self):
        data1 = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=Frequency.DAILY)

        data2 = self.bbg_provider.get_price(tickers=[self.MANY_TICKERS[1], self.MANY_TICKERS[0]],
                                            fields=self.SINGLE_PRICE_FIELD, start_date=self.START_DATE,
                                            end_date=self.END_DATE, frequency=Frequency.DAILY)

        assert_series_equal(data2.iloc[:, 0], data1.iloc[:, 1])
        assert_series_equal(data2.iloc[:, 1], data1.iloc[:, 0])

    def test_price_multiple_tickers_multiple_fields(self):
        # testing for single date (start_date and end_date are the same)
        data = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=Frequency.DAILY)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)

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
        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_FIELDS)

    def test_historical_single_ticker_single_field_list1(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.bbg_provider.get_history(tickers=[self.SINGLE_TICKER], fields=[self.SINGLE_FIELD],
                                             start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertIsInstance(data, QFDataArray)
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

    # =========================== Test get_current_values method =======================================================

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

    # =========================== Test QFDataArray type ====================================================

    def test_qf_dataarray_dtype_for_nan_volume(self):
        """ The tested ticker does not have any volume data within the given period. In this case it has to be
        checked if the dtype of QFDataArray would be correctly casted to float64 or to object. """
        tickers = [BloombergTicker("FMIM10 Index")]
        start_date = str_to_date("2010-01-14")
        end_date = str_to_date("2010-01-19")

        data_array = self.bbg_provider.get_price(tickers, [PriceField.Close, PriceField.Volume], start_date, end_date,
                                                 Frequency.DAILY)
        self.assertEqual(data_array.dtype, np.float64)


if __name__ == '__main__':
    unittest.main()
