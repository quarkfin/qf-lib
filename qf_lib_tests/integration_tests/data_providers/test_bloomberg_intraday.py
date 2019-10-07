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
import os
import unittest

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value, CachedValueException
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_series_equal
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


class TestBloombergIntraday(unittest.TestCase):
    LOAD_START_DATE = str_to_date('2019-05-15 13:00:00.0', DateFormat.FULL_ISO)
    START_DATE = str_to_date('2019-08-15 14:00:00.0', DateFormat.FULL_ISO)
    END_DATE = str_to_date('2019-08-15 14:45:00.0', DateFormat.FULL_ISO)
    SINGLE_FIELD = 'PX_LAST'
    MANY_FIELDS = ['PX_LAST', 'PX_OPEN', 'PX_HIGH']

    SINGLE_TICKER = BloombergTicker('IBM US Equity')
    MANY_TICKERS = [BloombergTicker('IBM US Equity'), BloombergTicker('AAPL US Equity')]
    SINGLE_PRICE_FIELD = PriceField.Close
    MANY_PRICE_FIELDS = [PriceField.Close, PriceField.Open, PriceField.High]

    FREQUENCY = Frequency.MIN_1
    NUM_OF_SAMPLES = 45

    history_provider = None
    price_provider = None

    @classmethod
    def setUpClass(cls):
        cls.history_provider = cls.setUpDataProvider('get_history')
        cls.price_provider = cls.setUpDataProvider('get_price')

    @classmethod
    def setUpDataProvider(cls, tested_function_name, frequency=Frequency.MIN_1):
        # configure the data provider
        input_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(input_dir,
                                'Bloomberg_intraday_frequency_{}_{}.cache'.format(
                                    frequency,
                                    tested_function_name)
                                )

        def get_data_provider():
            if bbg_provider.connected:
                # Load the data with 1 minute frequency
                tested_function = getattr(bbg_provider, tested_function_name)
                FIELDS = cls.MANY_FIELDS if tested_function_name == 'get_history' else cls.MANY_PRICE_FIELDS
                return tested_function(cls.MANY_TICKERS, FIELDS, cls.LOAD_START_DATE, cls.END_DATE, frequency)
            else:
                raise CachedValueException

        prefetched_data = cached_value(get_data_provider, filepath)

        return PresetDataProvider(prefetched_data, cls.LOAD_START_DATE, cls.END_DATE, frequency) if \
            prefetched_data is not None else None


@unittest.skipIf(not os.path.exists('Bloomberg_intraday_frequency_1_get_history.cache') and
                 not bbg_provider.connected, "No data available")
class TestBloombergIntradayHistory(TestBloombergIntraday):

    def setUp(self):
        self.bbg_provider = self.history_provider

    def test_historical_single_ticker_single_field(self):
        # single ticker, single field; end_date by default now
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)

        self.assertIsInstance(data, QFSeries)
        self.assertEqual(len(data), self.NUM_OF_SAMPLES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    @unittest.skip
    def test_historical_single_ticker_single_field_higher_frequency(self):
        # single ticker, single field; end_date by default now
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=Frequency.MIN_15)

        self.assertIsInstance(data, QFSeries)
        self.assertEqual(len(data), 3)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_historical_single_ticker_multiple_fields(self):
        # single ticker, many fields
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=self.MANY_FIELDS,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, len(self.MANY_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_multiple_tickers_single_field(self):
        data = self.bbg_provider.get_history(tickers=self.MANY_TICKERS, fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)
        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_multiple_tickers_multiple_fields_one_bar(self):
        # testing for single bar
        TEMP_DATE_MIN = self.END_DATE - self.FREQUENCY.time_delta()
        data = self.bbg_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                             start_date=TEMP_DATE_MIN, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)
        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertEqual(list(data.index), self.MANY_TICKERS)
        self.assertEqual(list(data.columns), self.MANY_FIELDS)

    def test_historical_multiple_tickers_multiple_fields_many_dates(self):
        # testing for single date
        data = self.bbg_provider.get_history(tickers=self.MANY_TICKERS, fields=self.MANY_FIELDS,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)
        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, len(self.MANY_TICKERS), len(self.MANY_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_FIELDS)

    def test_historical_single_ticker_single_field_list1(self):
        # single ticker, single field
        data = self.bbg_provider.get_history(tickers=[self.SINGLE_TICKER], fields=[self.SINGLE_FIELD],
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)

        self.assertIsInstance(data, QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, 1, 1))

    def test_historical_single_ticker_single_field_list2(self):
        # single ticker, many fields
        data = self.bbg_provider.get_history(tickers=[self.SINGLE_TICKER], fields=self.SINGLE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, 1))
        self.assertEqual(list(data.columns), [self.SINGLE_TICKER])

    def test_historical_single_ticker_single_field_list3(self):
        # single ticker, many field
        data = self.bbg_provider.get_history(tickers=self.SINGLE_TICKER, fields=[self.SINGLE_FIELD],
                                             start_date=self.START_DATE, end_date=self.END_DATE,
                                             frequency=self.FREQUENCY)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, 1))
        self.assertEqual(list(data.columns), [self.SINGLE_FIELD])


@unittest.skipIf(not os.path.exists('Bloomberg_intraday_frequency_1_get_price.cache') and
                     not bbg_provider.connected, "No data available")
class TestBloombergIntradayPrice(TestBloombergIntraday):

    def setUp(self):
        self.bbg_provider = self.price_provider

    def test_price_single_ticker_single_field(self):
        # single ticker, single field
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=self.FREQUENCY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), self.NUM_OF_SAMPLES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_single_ticker_multiple_fields(self):
        # single ticker, many fields
        data = self.bbg_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=self.FREQUENCY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, len(self.MANY_PRICE_FIELDS)))
        self.assertEqual(list(data.columns), self.MANY_PRICE_FIELDS)

    def test_price_multiple_tickers_single_field(self):
        data = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=self.FREQUENCY)

        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_price_multiple_tickers_single_field_order(self):
        data1 = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=self.FREQUENCY)

        data2 = self.bbg_provider.get_price(tickers=[self.MANY_TICKERS[1], self.MANY_TICKERS[0]],
                                            fields=self.SINGLE_PRICE_FIELD, start_date=self.START_DATE,
                                            end_date=self.END_DATE, frequency=self.FREQUENCY)

        assert_series_equal(data2.iloc[:, 0], data1.iloc[:, 1])
        assert_series_equal(data2.iloc[:, 1], data1.iloc[:, 0])

    def test_price_multiple_tickers_multiple_fields(self):
        # testing for single date
        data = self.bbg_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                           start_date=self.START_DATE, end_date=self.END_DATE,
                                           frequency=self.FREQUENCY)

        self.assertEqual(type(data), QFDataArray)
        self.assertEqual(data.shape, (self.NUM_OF_SAMPLES, len(self.MANY_TICKERS), len(self.MANY_PRICE_FIELDS)))
        self.assertIsInstance(data.dates.to_index(), pd.DatetimeIndex)
        self.assertEqual(list(data.tickers), self.MANY_TICKERS)
        self.assertEqual(list(data.fields), self.MANY_PRICE_FIELDS)


if __name__ == '__main__':
    unittest.main()
