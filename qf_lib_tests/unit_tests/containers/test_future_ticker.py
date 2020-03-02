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

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings


class CustomTicker(Ticker):
    def from_string(self, ticker_str):
        pass


class CustomFutureTicker(FutureTicker, CustomTicker):
    def belongs_to_family(self, ticker: CustomTicker) -> bool:
        pass

    def _get_futures_chain_tickers(self):
        tickers = [
            CustomTicker("A"),
            CustomTicker("B"),
            CustomTicker("C"),
            CustomTicker("D"),
            CustomTicker("E"),
            CustomTicker("F"),
            CustomTicker("G")
        ]

        exp_dates = [
            str_to_date('2017-11-13'),
            str_to_date('2017-12-15'),
            str_to_date('2018-01-12'),
            str_to_date('2018-02-13'),
            str_to_date('2018-03-15'),
            str_to_date('2018-04-14'),
            str_to_date('2018-05-13')
        ]

        return QFSeries(data=tickers, index=exp_dates)


class TestSeries(unittest.TestCase):

    def setUp(self):
        self.timer = SettableTimer(initial_time=str_to_date('2017-01-01'))
        settings = get_test_settings()
        self.bbg_provider = BloombergDataProvider(settings)

    def test_valid_ticker_1(self):
        future_ticker = CustomFutureTicker("Custom", "CT{} Custom", 1, 5, 500)
        future_ticker.initialize_data_provider(self.timer, self.bbg_provider)

        # '2017-12-15' is the official expiration date of CustomTicker:B, setting the days_before_exp_date equal to
        # 5 forces the expiration to occur on the 11th ('2017-12-15' - 5 days = '2017-12-10' is the last day of old
        # contract).
        self.timer.set_current_time(str_to_date('2017-12-05'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("B"))

        self.timer.set_current_time(str_to_date('2017-12-10'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("B"))

        self.timer.set_current_time(str_to_date('2017-12-11'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("C"))

    def test_valid_ticker_2(self):
        # Test the 2nd contract instead of front one

        future_ticker = CustomFutureTicker("Custom", "CT{} Custom", 2, 5, 500)
        future_ticker.initialize_data_provider(self.timer, self.bbg_provider)

        self.timer.set_current_time(str_to_date('2017-12-05'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("C"))

        self.timer.set_current_time(str_to_date('2017-12-10'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("C"))

        self.timer.set_current_time(str_to_date('2017-12-11'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("D"))

    def test_valid_ticker_3(self):
        future_ticker = CustomFutureTicker("Custom", "CT{} Custom", 1, 45, 500)
        future_ticker.initialize_data_provider(self.timer, self.bbg_provider)

        self.timer.set_current_time(str_to_date('2017-11-28'))
        # '2017-11-28' + 45 days = '2018-01-12' - the front contract will be equal to CustomTicker:D
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("C"))

        self.timer.set_current_time(str_to_date('2017-11-29'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("D"))

        self.timer.set_current_time(str_to_date('2017-12-05'))
        # '2017-12-05' + 45 days = '2018-01-19' - the front contract will be equal to CustomTicker:D
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("D"))

    def test_valid_ticker_4(self):
        future_ticker = CustomFutureTicker("Custom", "CT{} Custom", 2, 45, 500)
        future_ticker.initialize_data_provider(self.timer, self.bbg_provider)

        self.timer.set_current_time(str_to_date('2017-11-28'))
        # '2017-11-28' + 45 days = '2018-01-12' - the front contract will be equal to CustomTicker:D
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("D"))

        self.timer.set_current_time(str_to_date('2017-11-29'))
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("E"))

        self.timer.set_current_time(str_to_date('2017-12-05'))
        # '2017-12-05' + 45 days = '2018-01-19' - the front contract will be equal to CustomTicker:D
        self.assertEqual(future_ticker.get_current_specific_ticker(), CustomTicker("E"))


if __name__ == '__main__':
    unittest.main()
