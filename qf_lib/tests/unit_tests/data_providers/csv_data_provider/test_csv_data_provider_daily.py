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
from datetime import datetime
from pathlib import Path
from unittest import TestCase
import pandas as pd
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.csv.csv_data_provider import CSVDataProvider
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestCSVDataProviderDaily(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.start_date = datetime(2021, 1, 1)
        cls.end_date = datetime(2021, 3, 31)

        cls.number_of_data_bars = 90
        cls.fields = ['Open', 'High', 'Low', 'Close', 'Volume']
        cls.field_to_price_field_dict = {
            'Open': PriceField.Open,
            'High': PriceField.High,
            'Low': PriceField.Low,
            'Close': PriceField.Close,
            'Volume': PriceField.Volume,
        }
        cls.price_fields = PriceField.ohlcv()

        cls.ticker = DummyTicker('BTCBUSD', SecurityType.CRYPTO)
        cls.tickers = [DummyTicker('BTCBUSD', SecurityType.CRYPTO), DummyTicker('ETHBUSD')]

        cls.path = str(Path(__file__).parent / Path('input_data'))
        cls.data_provider = CSVDataProvider(cls.path, cls.tickers, 'Open time', cls.field_to_price_field_dict,
                                            cls.fields, cls.start_date, cls.end_date,
                                            Frequency.DAILY, )

    def test_cached_parameters(self):
        self.assertCountEqual(self.data_provider.cached_tickers,
                              {DummyTicker('BTCBUSD', SecurityType.CRYPTO), DummyTicker('ETHBUSD')})
        self.assertCountEqual(self.data_provider.cached_fields, self.fields + PriceField.ohlcv())

    def test_get_price_single_ticker_many_fields(self):
        prices = self.data_provider.get_price(self.ticker, self.price_fields, self.start_date, self.end_date)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(self.price_fields)))
        self.assertEqual(Frequency.infer_freq(prices.index), Frequency.DAILY)

    def test_get_history_single_ticker_many_fields(self):
        df = self.data_provider.get_history(self.ticker, self.fields, self.start_date, self.end_date)

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (self.number_of_data_bars, len(self.fields)))
        self.assertEqual(Frequency.infer_freq(df.index), Frequency.DAILY)

    def test_get_price_single_ticker_many_fields_single_date(self):
        date = str_to_date('2021-02-01')

        prices = self.data_provider.get_price(self.ticker, self.price_fields, date, date)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.price_fields),))

    def test_get_history_single_ticker_many_fields_single_date(self):
        date = str_to_date('2021-02-01')

        df = self.data_provider.get_history(self.ticker, self.fields, date, date)

        self.assertEqual(type(df), QFSeries)
        self.assertEqual(df.shape, (len(self.price_fields),))

    def test_get_price_single_ticker_single_field_many_dates(self):
        prices = self.data_provider.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (self.number_of_data_bars,))

    def test_get_history_single_ticker_single_field_many_dates(self):
        df = self.data_provider.get_history(self.ticker, 'Close', self.start_date, self.end_date)

        self.assertEqual(type(df), QFSeries)
        self.assertEqual(df.shape, (self.number_of_data_bars,))

    def test_get_price_single_ticker_single_field_single_date(self):
        date = str_to_date('2021-02-01')

        prices = self.data_provider.get_price(self.ticker, PriceField.Close, date, date)
        self.assertEqual(prices, 33528.41)

    def test_get_history_sigle_ticker_single_field_single_date(self):
        date = str_to_date('2021-02-01')

        prices = self.data_provider.get_history(self.ticker, 'Close', date, date)
        self.assertEqual(prices, 33528.41)

    def test_get_price_many_tickers_many_fields_many_dates(self):
        prices = self.data_provider.get_price(self.tickers, self.price_fields, self.start_date, self.end_date)

        self.assertEqual(type(prices), QFDataArray)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(self.tickers), len(self.price_fields)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.dates.values)), Frequency.DAILY)

    def test_get_history_many_tickers_many_fields_many_dates(self):
        df = self.data_provider.get_history(self.tickers, self.fields, self.start_date, self.end_date)

        self.assertEqual(type(df), QFDataArray)
        self.assertEqual(df.shape, (self.number_of_data_bars, len(self.tickers), len(self.price_fields)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(df.dates.values)), Frequency.DAILY)

    def test_get_price_many_tickers_single_field_many_dates(self):
        prices = self.data_provider.get_price(self.tickers, PriceField.Close, self.start_date, self.end_date)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(self.tickers)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.index)), Frequency.DAILY)

    def test_get_history_many_tickers_single_field_many_dates(self):
        df = self.data_provider.get_history(self.tickers, 'Close', self.start_date, self.end_date)

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (self.number_of_data_bars, len(self.tickers)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(df.index)), Frequency.DAILY)

    def test_get_price_many_tickers_many_fields_single_date(self):
        date = str_to_date('2021-02-01')
        prices = self.data_provider.get_price(self.tickers, self.price_fields, date, date)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (len(self.tickers), len(self.price_fields)))

    def test_get_history_many_tickers_many_fields_single_date(self):
        date = str_to_date('2021-02-01')
        df = self.data_provider.get_history(self.tickers, self.fields, date, date)

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (len(self.tickers), len(self.price_fields)))

    def test_get_price_many_tickers_single_field_single_date(self):
        date = str_to_date('2021-02-01')
        prices = self.data_provider.get_price(self.tickers, PriceField.Close, date, date)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.tickers),))

    def test_get_history_many_tickers_single_field_single_date(self):
        date = str_to_date('2021-02-01')
        df = self.data_provider.get_history(self.tickers, 'Close', date, date)

        self.assertEqual(type(df), QFSeries)
        self.assertEqual(df.shape, (len(self.tickers),))
