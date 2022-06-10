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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import HaverTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.haver import HaverDataProvider
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
haver_provider = HaverDataProvider(settings)
haver_provider.connect()


@unittest.skipIf(not haver_provider.connected, "No Haver connection, skipping tests")
class TestHaverDataProvider(unittest.TestCase):
    START_DATE = str_to_date('2015-01-01')
    END_DATE = str_to_date('2017-01-01')
    INVALID_TICKER1 = HaverTicker('ABC', 'EUDATA')
    INVALID_TICKER2 = HaverTicker('N023VSGX', 'XYZ')
    INVALID_TICKERS = [INVALID_TICKER1, HaverTicker('N023VZCE', 'EUDATA'), INVALID_TICKER2]

    SINGLE_TICKER = HaverTicker('N023VSGX', 'EUDATA')
    MANY_TICKERS = [HaverTicker('N023VSGX', 'EUDATA'), HaverTicker('N023VZCE', 'EUDATA'),
                    HaverTicker('RECESSQ2', 'USECON')]
    NUM_OF_DATES = 25
    MAX_DATES = 185

    SINGLE_PRICE_FIELD = PriceField.Close

    def setUp(self):
        self.data_provider = haver_provider

    # =========================== Test invalid ticker ==========================================================

    def test_price_single_invalid_ticker(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.data_provider.get_price(tickers=self.INVALID_TICKER1, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), 0)
        self.assertEqual(data.name, self.INVALID_TICKER1.as_string())

        data = self.data_provider.get_price(tickers=self.INVALID_TICKER2, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), 0)
        self.assertEqual(data.name, self.INVALID_TICKER2.as_string())

    def test_price_many_invalid_tickers(self):
        # single ticker, single field; end_date by default now, frequency by default DAILY, currency by default None
        data = self.data_provider.get_price(tickers=self.INVALID_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.INVALID_TICKERS)))
        self.assertEqual(list(data.columns), self.INVALID_TICKERS)

    # =========================== Test get_price method ==========================================================

    def test_price_single_ticker(self):
        data = self.data_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=Frequency.DAILY)

        self.assertIsInstance(data, PricesSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_price_multiple_tickers(self):
        data = self.data_provider.get_price(tickers=self.MANY_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                            start_date=self.START_DATE, end_date=self.END_DATE,
                                            frequency=Frequency.DAILY)
        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    # =========================== Test get_history method ==========================================================

    def test_historical_single_ticker(self):
        data = self.data_provider.get_history(tickers=self.SINGLE_TICKER,
                                              start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertIsInstance(data, QFSeries)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_historical_multiple_tickers(self):
        data = self.data_provider.get_history(tickers=self.MANY_TICKERS,
                                              start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(type(data), QFDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(self.MANY_TICKERS)))
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_single_ticker_no_date(self):
        data = self.data_provider.get_history(tickers=self.SINGLE_TICKER)
        self.assertIsInstance(data, QFSeries)
        self.assertTrue(len(data) >= self.MAX_DATES)
        self.assertEqual(data.name, self.SINGLE_TICKER.as_string())

    def test_historical_multiple_tickers_no_date(self):
        data = self.data_provider.get_history(tickers=self.MANY_TICKERS)

        self.assertEqual(type(data), QFDataFrame)
        self.assertTrue(len(data) >= self.MAX_DATES)
        self.assertEqual(list(data.columns), self.MANY_TICKERS)

    def test_historical_single_ticker_list(self):
        data = self.data_provider.get_history(tickers=[self.SINGLE_TICKER],
                                              start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertIsInstance(data, QFDataFrame)
        self.assertEqual(len(data), self.NUM_OF_DATES)
        self.assertEqual(list(data.columns), [self.SINGLE_TICKER])

    def test_historical_single_ticker_no_end_date(self):
        data = self.data_provider.get_history(tickers=self.SINGLE_TICKER, start_date=self.START_DATE)
        self.assertTrue(len(data) >= self.NUM_OF_DATES)

    def test_historical_single_ticker_no_dates(self):
        data = self.data_provider.get_history(tickers=self.SINGLE_TICKER)
        self.assertTrue(len(data) >= self.NUM_OF_DATES)


if __name__ == '__main__':
    unittest.main()
