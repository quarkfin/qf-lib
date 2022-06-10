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

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()

data_provider = GeneralPriceProvider(bbg_provider)
timer = SettableTimer()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestGeneralPriceProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frequency = Frequency.DAILY
        cls.tickers = [
            BloombergFutureTicker("Cotton", "CT{} Comdty", 1, 3),
            BloombergFutureTicker("Corn", 'C {} Comdty', 1, 5, 50, "HMUZ")]

        timer.set_current_time(str_to_date('2017-12-20'))

        for ticker in cls.tickers:
            ticker.initialize_data_provider(timer, bbg_provider)

        cls.start_date = str_to_date('2015-10-08')
        cls.end_date = str_to_date('2017-12-20')

        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 00, "second": 0, "microsecond": 0})

    def test_get_futures_chain_tickers(self):
        fut_chain_dict = data_provider.get_futures_chain_tickers(self.tickers, ExpirationDateField.all_dates())
        bbg_fut_chain_dict = bbg_provider.get_futures_chain_tickers(self.tickers, ExpirationDateField.all_dates())

        for ticker in self.tickers:
            self.assertCountEqual(fut_chain_dict[ticker], bbg_fut_chain_dict[ticker])
