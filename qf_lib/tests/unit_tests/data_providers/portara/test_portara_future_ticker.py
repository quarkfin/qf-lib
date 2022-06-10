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

from pandas import concat

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import PortaraTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.portara_future_ticker import PortaraFutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.data_providers.portara.portara_data_provider import PortaraDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal


class TestPortaraFutureTicker(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.start_date = str_to_date('2021-05-18')
        cls.end_date = str_to_date('2021-06-28')

        cls.future_ticker_1 = PortaraFutureTicker("", "AB{}", 1, 1)
        cls.future_ticker_2 = PortaraFutureTicker("", "ABCD{}", 1, 11, 17)

        cls.futures_path = str(Path(__file__).parent / Path('input_data') / Path('Futures'))

    def setUp(self) -> None:
        self.data_provider = PortaraDataProvider(self.futures_path, [self.future_ticker_1, self.future_ticker_2],
                                                 PriceField.ohlcv(), self.start_date, self.end_date, Frequency.DAILY)

    def test_get_current_specific_ticker(self):
        timer = SettableTimer()
        self.future_ticker_1.initialize_data_provider(timer, self.data_provider)

        timer.set_current_time(str_to_date("2021-03-18"))
        specific_ticker = self.future_ticker_1.get_current_specific_ticker()
        self.assertEqual(specific_ticker, PortaraTicker("AB2021M", SecurityType.FUTURE, 1))

        timer.set_current_time(str_to_date("2021-06-14"))
        specific_ticker = self.future_ticker_1.get_current_specific_ticker()
        self.assertEqual(specific_ticker, PortaraTicker("AB2021M", SecurityType.FUTURE, 1))

        timer.set_current_time(str_to_date("2021-06-15"))
        specific_ticker = self.future_ticker_1.get_current_specific_ticker()
        self.assertEqual(specific_ticker, PortaraTicker("AB2021U", SecurityType.FUTURE, 1))

        timer.set_current_time(datetime(2021, 12, 14, 23, 59))
        specific_ticker = self.future_ticker_1.get_current_specific_ticker()
        self.assertEqual(specific_ticker, PortaraTicker("AB2021Z", SecurityType.FUTURE, 1))

    def test_belongs_to_family(self):
        self.assertTrue(self.future_ticker_1.belongs_to_family(PortaraTicker("AB2021M", SecurityType.FUTURE, 1)))
        self.assertTrue(self.future_ticker_1.belongs_to_family(PortaraTicker("AB1921K", SecurityType.FUTURE, 1)))
        self.assertTrue(self.future_ticker_1.belongs_to_family(PortaraTicker("AB2020Z", SecurityType.FUTURE, 1)))
        self.assertTrue(self.future_ticker_2.belongs_to_family(PortaraTicker("ABCD1234H", SecurityType.FUTURE, 17)))

        self.assertFalse(self.future_ticker_1.belongs_to_family(PortaraTicker("ABCD1234H", SecurityType.FUTURE, 17)))
        self.assertFalse(self.future_ticker_1.belongs_to_family(PortaraTicker("AB2020Z", SecurityType.FUTURE, 13)))
        self.assertFalse(self.future_ticker_2.belongs_to_family(PortaraTicker("AB2021M", SecurityType.FUTURE, 1)))
        self.assertFalse(self.future_ticker_2.belongs_to_family(PortaraTicker("AB1921K", SecurityType.FUTURE, 1)))
        self.assertFalse(self.future_ticker_2.belongs_to_family(PortaraTicker("AB2020Z", SecurityType.FUTURE, 1)))

    def test_designated_contracts(self):
        future_ticker = PortaraFutureTicker("", "AB{}", 1, 1, designated_contracts="MZ")

        timer = SettableTimer()
        future_ticker.initialize_data_provider(timer, self.data_provider)

        timer.set_current_time(str_to_date("2021-06-15"))
        specific_ticker = future_ticker.get_current_specific_ticker()
        self.assertEqual(specific_ticker, PortaraTicker("AB2021Z", SecurityType.FUTURE, 1))

    def test_futures_chain_without_adjustment(self):
        timer = SettableTimer(self.end_date)
        self.future_ticker_1.initialize_data_provider(timer, self.data_provider)

        futures_chain = FuturesChain(self.future_ticker_1, self.data_provider, FuturesAdjustmentMethod.NTH_NEAREST)

        # AB2021M is the current specific ticker till 2021-06-14 inclusive, afterwards the AB2021U
        start_date = str_to_date("2021-06-13")
        end_date = str_to_date("2021-06-17")
        fields = PriceField.ohlcv()
        prices = futures_chain.get_price(fields, start_date, end_date, Frequency.DAILY)

        prices_m_contract = self.data_provider.get_price(PortaraTicker("AB2021M", SecurityType.FUTURE, 1), fields,
                                                         start_date, str_to_date("2021-06-14"), Frequency.DAILY)
        prices_u_contract = self.data_provider.get_price(PortaraTicker("AB2021U", SecurityType.FUTURE, 1), fields,
                                                         str_to_date("2021-06-15"), end_date, Frequency.DAILY)

        assert_dataframes_equal(prices, concat([prices_m_contract, prices_u_contract]), check_names=False)
