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

from qf_lib.backtesting.data_handler.daily_data_handler import DailyDataHandler
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider
from qf_lib.tests.integration_tests.connect_to_data_provider import get_data_provider


class TestPresetDataProviderWithFutures(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.end_date = str_to_date('2015-10-08')
        cls.start_date = cls.end_date - RelativeDelta(years=2)

        cls.timer = SettableTimer(cls.end_date)

        cls.frequency = Frequency.DAILY
        cls.TICKER_1 = BloombergFutureTicker("Cotton", "CT{} Comdty", 1, 3)
        cls.TICKER_2 = BloombergFutureTicker("Corn", 'C {} Comdty', 1, 5)

    def setUp(self):
        try:
            self.data_provider = get_data_provider()
        except Exception as e:
            raise self.skipTest(e)

        self.TICKER_1.initialize_data_provider(self.timer, self.data_provider)
        self.TICKER_2.initialize_data_provider(self.timer, self.data_provider)
        data_provider = PrefetchingDataProvider(self.data_provider,
                                                self.TICKER_2,
                                                PriceField.ohlcv(),
                                                self.start_date,
                                                self.end_date,
                                                self.frequency)

        self.timer.set_current_time(self.end_date)
        self.data_handler = DailyDataHandler(data_provider, self.timer)

    def test_data_provider_init(self):
        self.assertCountEqual(self.data_handler.data_provider.supported_ticker_types(),
                              {BloombergTicker})

    def test_get_futures_chain_1_ticker(self):
        bbg_fut_chain_tickers = self.data_provider.get_futures_chain_tickers(
            self.TICKER_2, ExpirationDateField.all_dates())
        preset_fut_chain_tickers = self.data_handler.data_provider.get_futures_chain_tickers(
            self.TICKER_2, ExpirationDateField.all_dates())

        self.assertCountEqual(bbg_fut_chain_tickers[self.TICKER_2], preset_fut_chain_tickers[self.TICKER_2])

    def test_get_futures_chain_multiple_tickers(self):
        tickers = [self.TICKER_2]
        bbg_fut_chain_tickers = self.data_provider.get_futures_chain_tickers(tickers, ExpirationDateField.all_dates())
        preset_fut_chain_tickers = self.data_handler.data_provider.get_futures_chain_tickers(
            tickers, ExpirationDateField.all_dates())

        for ticker in tickers:
            self.assertCountEqual(bbg_fut_chain_tickers[ticker], preset_fut_chain_tickers[ticker])
