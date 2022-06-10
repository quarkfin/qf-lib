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
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.csv.csv_data_provider import CSVDataProvider
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestCSVDataProviderIntraday(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.start_date = datetime(2020, 12, 30)
        cls.end_date = datetime(2020, 12, 30, 1, 33)

        cls.fields = ['Open', 'High', 'Low', 'Close', 'Volume']
        cls.field_to_price_field_dict = {
            'Open': PriceField.Open,
            'High': PriceField.High,
            'Low': PriceField.Low,
            'Close': PriceField.Close,
            'Volume': PriceField.Volume,
        }
        cls.price_fields = PriceField.ohlcv()

        cls.ticker = DummyTicker('BTCBUSD')
        cls.tickers = [DummyTicker('BTCBUSD'), DummyTicker('ETHBUSD')]

        cls.path = str(Path(__file__).parent / Path('input_data'))

        cls.data_provider = CSVDataProvider(cls.path, cls.tickers, 'Open time', cls.field_to_price_field_dict,
                                            cls.fields, cls.start_date, cls.end_date, Frequency.MIN_1)

    def test_get_price_single_ticker_many_fields(self):
        prices = self.data_provider.get_price(self.ticker, self.price_fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape[1], len(self.price_fields))
        self.assertEqual(Frequency.infer_freq(prices.index), Frequency.MIN_1)

    def test_agg_get_price_single_ticker_many_fields(self):
        prices = self.data_provider.get_price(self.ticker, self.price_fields, self.start_date, self.end_date, Frequency.MIN_15)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape[1], len(self.price_fields))
        self.assertEqual(Frequency.infer_freq(prices.index), Frequency.MIN_15)

    def test_get_history_single_ticker_many_fields(self):
        df = self.data_provider.get_history(self.ticker, self.fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape[1], len(self.price_fields))
        self.assertEqual(Frequency.infer_freq(df.index), Frequency.MIN_1)

    def test_get_price_single_ticker_many_fields_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)

        prices = self.data_provider.get_price(self.ticker, self.price_fields, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.price_fields),))

    def test_agg_get_price_single_ticker_many_fields_single_date(self):
        date = datetime(2020, 12, 30, 1, 15)

        prices = self.data_provider.get_price(self.ticker, self.price_fields, date, date + RelativeDelta(minutes=1),
                                              Frequency.MIN_15)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.price_fields),))

    def test_get_history_single_ticker_many_fields_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)

        df = self.data_provider.get_history(self.ticker, self.fields, date, date, Frequency.MIN_1)

        self.assertEqual(type(df), QFSeries)
        self.assertEqual(df.shape, (len(self.fields),))

    def test_get_price_single_ticker_single_field_many_dates(self):
        prices = self.data_provider.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date,
                                              Frequency.MIN_1)

        self.assertEqual(type(prices), PricesSeries)

    def test_agg_get_price_single_ticker_single_field_many_dates(self):
        prices = self.data_provider.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date,
                                              Frequency.MIN_15)

        self.assertEqual(type(prices), PricesSeries)

    def test_get_history_single_ticker_single_field_many_dates(self):
        df = self.data_provider.get_history(self.ticker, 'Close', self.start_date, self.end_date,
                                            Frequency.MIN_1)

        self.assertEqual(type(df), QFSeries)

    def test_get_price_single_ticker_single_field_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)

        prices = self.data_provider.get_price(self.ticker, PriceField.Close, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), float)
        self.assertEqual(prices, 27647.41)

    def test_agg_get_price_single_ticker_single_field_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)

        prices = self.data_provider.get_price(self.ticker, PriceField.Close, date, date, Frequency.MIN_5)

        self.assertEqual(type(prices), float)
        self.assertEqual(prices, 27647.41)

    def test_get_history_single_ticker_single_field_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)

        df = self.data_provider.get_history(self.ticker, 'Close', date, date, Frequency.MIN_1)

        self.assertEqual(type(df), float)
        self.assertEqual(df, 27647.41)

    def test_get_price_many_tickers_many_fields_many_dates(self):
        prices = self.data_provider.get_price(self.tickers, self.price_fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), QFDataArray)
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.dates.values)), Frequency.MIN_1)

    def test_agg_get_price_many_tickers_many_fields_many_dates(self):
        prices = self.data_provider.get_price(self.tickers, self.price_fields, self.start_date, self.end_date, Frequency.MIN_15)

        self.assertEqual(type(prices), QFDataArray)
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.dates.values)), Frequency.MIN_15)

    def test_get_history_many_tickers_many_fields_many_dates(self):
        df = self.data_provider.get_history(self.tickers, self.fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(df), QFDataArray)
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(df.dates.values)), Frequency.MIN_1)

    def test_get_price_many_tickers_single_field_many_dates(self):
        prices = self.data_provider.get_price(self.tickers, PriceField.Close, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.index)), Frequency.MIN_1)

    def test_agg_get_price_many_tickers_single_field_many_dates(self):
        prices = self.data_provider.get_price(self.tickers, PriceField.Close, self.start_date, self.end_date, Frequency.MIN_15)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.index)), Frequency.MIN_15)

    def test_get_history_many_tickers_single_field_many_dates(self):
        df = self.data_provider.get_history(self.tickers, 'Close', self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(df.index)), Frequency.MIN_1)

    def test_get_price_many_tickers_many_fields_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)
        prices = self.data_provider.get_price(self.tickers, self.price_fields, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (len(self.tickers), len(self.price_fields)))

    def test_agg_get_price_many_tickers_many_fields_single_date(self):
        date = datetime(2020, 12, 30, 1, 15)
        prices = self.data_provider.get_price(self.tickers, self.price_fields, date, date + RelativeDelta(minutes=1),
                                              Frequency.MIN_15)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (len(self.tickers), len(self.price_fields)))

    def test_get_history_many_tickers_many_fields_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)
        df = self.data_provider.get_history(self.tickers, self.fields, date, date, Frequency.MIN_1)

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (len(self.tickers), len(self.fields)))

    def test_get_price_many_tickers_single_field_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)
        prices = self.data_provider.get_price(self.tickers, PriceField.Close, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.tickers),))

    def test_agg_get_price_many_tickers_single_field_single_date(self):

        date = datetime(2020, 12, 30, 1, 15)
        prices = self.data_provider.get_price(self.tickers, PriceField.Close, date, date + RelativeDelta(minutes=1),
                                              Frequency.MIN_15)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.tickers),))

    def test_get_history_many_tickers_single_field_single_date(self):
        date = datetime(2020, 12, 30, 1, 5)
        df = self.data_provider.get_history(self.tickers, 'Close', date, date, Frequency.MIN_1)

        self.assertEqual(type(df), QFSeries)
        self.assertEqual(df.shape, (len(self.tickers),))
