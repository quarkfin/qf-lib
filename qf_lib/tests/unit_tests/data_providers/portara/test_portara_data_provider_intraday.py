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

from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import PortaraTicker
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.portara_future_ticker import PortaraFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.portara.portara_data_provider import PortaraDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestPortaraDataProviderIntraday(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.start_date = datetime(2021, 6, 11, 17, 13)
        cls.end_date = datetime(2021, 6, 14, 8, 46)

        cls.number_of_data_bars = 29
        cls.fields = PriceField.ohlcv()

        cls.ticker = PortaraTicker('AB', SecurityType.FUTURE, 1)
        cls.tickers = [PortaraTicker('AB', SecurityType.FUTURE, 1), PortaraTicker('ABCD', SecurityType.FUTURE, 7)]

        cls.future_ticker = PortaraFutureTicker("", "AB{}", 1, 1)
        cls.future_tickers = [PortaraFutureTicker("", "AB{}", 1, 1), PortaraFutureTicker("", "ABCD{}", 1, 7)]

        cls.futures_path = str(Path(__file__).parent / Path('input_data') / Path('Futures'))

    def get_data_provider(self, tickers, fields) -> PortaraDataProvider:
        return PortaraDataProvider(self.futures_path, tickers, fields, self.start_date, self.end_date, Frequency.MIN_1)

    def test_get_price_single_ticker_many_fields_many_dates(self):
        data_provider = self.get_data_provider(self.ticker, self.fields)
        prices = data_provider.get_price(self.ticker, self.fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(self.fields)))
        self.assertEqual(Frequency.infer_freq(prices.index), Frequency.MIN_1)

    def test_get_price_single_ticker_many_fields_single_date(self):
        date = datetime(2021, 6, 11, 17, 28)
        data_provider = self.get_data_provider(self.ticker, self.fields)

        prices = data_provider.get_price(self.ticker, self.fields, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.fields),))

    def test_get_price_single_ticker_single_field_many_dates(self):
        data_provider = self.get_data_provider(self.ticker, PriceField.Close)
        prices = data_provider.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (self.number_of_data_bars,))

    def test_get_price_single_ticker_single_field_single_date(self):
        date = datetime(2021, 6, 11, 17, 28)
        data_provider = self.get_data_provider(self.ticker, PriceField.Close)

        prices = data_provider.get_price(self.ticker, PriceField.Close, date, date, Frequency.MIN_1)
        self.assertEqual(type(prices), int)
        self.assertEqual(prices, 61640)

    def test_get_price_many_tickers_many_fields_many_dates(self):
        data_provider = self.get_data_provider(self.tickers, self.fields)
        prices = data_provider.get_price(self.tickers, self.fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), QFDataArray)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(self.tickers), len(self.fields)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.dates.values)), Frequency.MIN_1)

    def test_get_price_many_tickers_single_field_many_dates(self):
        data_provider = self.get_data_provider(self.tickers, PriceField.Close)
        prices = data_provider.get_price(self.tickers, PriceField.Close, self.start_date, self.end_date,
                                         Frequency.MIN_1)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(self.tickers)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.index)), Frequency.MIN_1)

    def test_get_price_many_tickers_many_fields_single_date(self):
        date = datetime(2021, 6, 11, 17, 28)
        data_provider = self.get_data_provider(self.tickers, self.fields)
        prices = data_provider.get_price(self.tickers, self.fields, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesDataFrame)
        self.assertEqual(prices.shape, (len(self.tickers), len(self.fields)))

    def test_get_price_many_tickers_single_field_single_date(self):
        date = datetime(2021, 6, 11, 17, 28)
        data_provider = self.get_data_provider(self.tickers, PriceField.Close)
        prices = data_provider.get_price(self.tickers, PriceField.Close, date, date, Frequency.MIN_1)

        self.assertEqual(type(prices), PricesSeries)
        self.assertEqual(prices.shape, (len(self.tickers),))

    def test_get_price_single_future_ticker_many_fields(self):
        data_provider = self.get_data_provider(self.future_ticker, self.fields)
        tickers_to_check = [PortaraTicker('AB2021M', SecurityType.FUTURE, 1),
                            PortaraTicker('AB2021U', SecurityType.FUTURE, 1)]

        prices = data_provider.get_price(tickers_to_check, self.fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), QFDataArray)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(tickers_to_check), len(self.fields)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.dates.values)), Frequency.MIN_1)
        self.assertCountEqual(prices.tickers.values, tickers_to_check)

    def test_get_price_many_future_tickers_many_fields(self):
        data_provider = self.get_data_provider(self.future_tickers, self.fields)

        tickers_to_check = [PortaraTicker('AB2021M', SecurityType.FUTURE, 1),
                            PortaraTicker('AB2021U', SecurityType.FUTURE, 1),
                            PortaraTicker('ABCD2021M', SecurityType.FUTURE, 7),
                            PortaraTicker('ABCD2021N', SecurityType.FUTURE, 7),
                            PortaraTicker('ABCD2021Q', SecurityType.FUTURE, 7)]
        prices = data_provider.get_price(tickers_to_check, self.fields, self.start_date, self.end_date, Frequency.MIN_1)

        self.assertEqual(type(prices), QFDataArray)
        self.assertEqual(prices.shape, (self.number_of_data_bars, len(tickers_to_check), len(self.fields)))
        self.assertEqual(Frequency.infer_freq(pd.to_datetime(prices.dates.values)), Frequency.MIN_1)
        self.assertCountEqual(prices.tickers.values, tickers_to_check)

    def test_get_fut_chain_single_future_ticker(self):
        data_provider = self.get_data_provider(self.future_ticker, self.fields)
        fut_chain = data_provider.get_futures_chain_tickers(self.future_ticker,
                                                            ExpirationDateField.LastTradeableDate)

        self.assertTrue(fut_chain)
        self.assertEqual(type(fut_chain), dict)
        self.assertEqual(type(fut_chain[self.future_ticker]), QFDataFrame)
        self.assertEqual(fut_chain[self.future_ticker].shape, (4, 1))

    def test_get_fut_chain_many_future_tickers(self):
        data_provider = self.get_data_provider(self.future_tickers, self.fields)
        fut_chain = data_provider.get_futures_chain_tickers(self.future_tickers,
                                                            ExpirationDateField.LastTradeableDate)

        self.assertTrue(fut_chain)
        self.assertEqual(type(fut_chain), dict)
        self.assertEqual(type(fut_chain[self.future_tickers[0]]), QFDataFrame)
        self.assertEqual(fut_chain[self.future_tickers[0]].shape, (4, 1))
        self.assertEqual(fut_chain[self.future_tickers[1]].shape, (3, 1))

    def test_get_price_aggregation_single_ticker(self):
        MarketOpenEvent.set_trigger_time({"hour": 17, "minute": 13, "second": 0, "microsecond": 0})

        dp = PortaraDataProvider(self.futures_path, self.ticker, PriceField.Close, self.start_date, self.end_date,
                                 Frequency.MIN_1)
        prices = dp.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date, Frequency.MIN_1)
        prices5 = dp.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date, Frequency.MIN_5)
        prices15 = dp.get_price(self.ticker, PriceField.Close, self.start_date, self.end_date, Frequency.MIN_15)

        self.assertTrue(len(prices5))
        self.assertEqual(type(prices5), PricesSeries)
        self.assertEqual(Frequency.infer_freq(prices5.index), Frequency.MIN_5)

        assert_series_equal(prices5, prices.loc[datetime(2021, 6, 11, 17, 15):].resample('5T').last().dropna(),
                            check_names=False)

        self.assertTrue(len(prices15))
        self.assertEqual(type(prices15), PricesSeries)
        assert_series_equal(prices15, prices.loc[datetime(2021, 6, 11, 17, 15):].resample('15T').last().dropna(),
                            check_names=False)
