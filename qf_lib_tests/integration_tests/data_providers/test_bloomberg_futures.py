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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestBloombergFutures(unittest.TestCase):

    frequency = Frequency.DAILY
    TICKER_1 = BloombergTicker("ESZ9 Index")  # expiry dates - Fridays
    TICKER_2 = BloombergTicker('C Z9 COMB Comdty')

    def _get_data(self):
        dictionary = bbg_provider.get_futures([self.TICKER_1, self.TICKER_2], self.start_date, self.end_date)
        return dictionary

    def setUp(self):
        self.end_date = str_to_date('2019-10-08')
        self.start_date = self.end_date - RelativeDelta(years=10)

        input_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(input_dir,
                                'Bloomberg_futures_frequency_{}.cache'.format(
                                    self.frequency)
                                )

        self.futures_chains_dict = cached_value(self._get_data, filepath)

    def test_get_ticker_1st_cotnract_1_day_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-12-16"): BloombergTicker('ESZ16 Index'),
            str_to_date("2017-03-17"): BloombergTicker('ESH17 Index')
        }

        futures_chain = self.futures_chains_dict[self.TICKER_1]
        self.assertEqual(FuturesChain, type(futures_chain))

        # Check dates before 2016-12-16
        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-11-11'), 1),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-12-15'), 1),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-12-15 23:55:00.0', DateFormat.FULL_ISO), 1),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        # On the expiry day, the next contract should be returned
        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-12-16'), 1),
                         exp_dates_to_ticker_str[str_to_date("2017-03-17")])

    def test_get_ticker_1st_cotnract_6_days_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-12-16"): BloombergTicker('ESZ16 Index'),
            str_to_date("2017-03-17"): BloombergTicker('ESH17 Index')
        }

        futures_chain = self.futures_chains_dict[self.TICKER_1]
        self.assertEqual(FuturesChain, type(futures_chain))

        # Check dates before 2016-12-16
        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-11-11'), 6),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-12-10'), 6),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-12-10 23:55:00.0', DateFormat.FULL_ISO), 6),
                         exp_dates_to_ticker_str[str_to_date("2016-12-16")])

        self.assertEqual(futures_chain.get_ticker(1, str_to_date('2016-12-16'), 6),
                         exp_dates_to_ticker_str[str_to_date("2017-03-17")])

    def test_get_ticker_2nd_cotnract_1_day_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-07-14"): BloombergTicker('C N16 Comdty'),
            str_to_date("2016-09-14"): BloombergTicker('C U16 Comdty'),
            str_to_date("2016-12-14"): BloombergTicker('C Z16 Comdty')
        }

        futures_chain = self.futures_chains_dict[self.TICKER_2]

        self.assertEqual(futures_chain.get_ticker(2, str_to_date('2016-06-03'), 1),
                         exp_dates_to_ticker_str[str_to_date("2016-09-14")])

        self.assertEqual(futures_chain.get_ticker(2, str_to_date('2016-07-13 23:59:59.0', DateFormat.FULL_ISO), 1),
                         exp_dates_to_ticker_str[str_to_date("2016-09-14")])

        self.assertEqual(futures_chain.get_ticker(2, str_to_date('2016-07-14'), 1),
                         exp_dates_to_ticker_str[str_to_date("2016-12-14")])

    def test_get_ticker_2nd_cotnract_6_days_before_exp_date(self):
        exp_dates_to_ticker_str = {
            str_to_date("2016-07-14"): BloombergTicker('C N16 Comdty'),
            str_to_date("2016-09-14"): BloombergTicker('C U16 Comdty'),
            str_to_date("2016-12-14"): BloombergTicker('C Z16 Comdty')
        }

        futures_chain = self.futures_chains_dict[self.TICKER_2]

        self.assertEqual(futures_chain.get_ticker(2, str_to_date('2016-06-03'), 6),
                         exp_dates_to_ticker_str[str_to_date("2016-09-14")])

        self.assertEqual(futures_chain.get_ticker(2, str_to_date('2016-07-08 23:59:59.0', DateFormat.FULL_ISO), 6),
                         exp_dates_to_ticker_str[str_to_date("2016-09-14")])

        self.assertEqual(futures_chain.get_ticker(2, str_to_date('2016-07-09'), 6),
                         exp_dates_to_ticker_str[str_to_date("2016-12-14")])
