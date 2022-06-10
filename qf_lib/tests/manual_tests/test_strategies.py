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

from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.tests.manual_tests import spx_with_stop_loss
from qf_lib.tests.manual_tests import futures_strategy
from qf_lib.tests.manual_tests import simple_ma_strategy
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings


class TestStrategies(unittest.TestCase):

    def setUp(self) -> None:
        settings = get_test_settings()
        self.data_provider = BloombergDataProvider(settings)
        self.data_provider.connect()

        if not self.data_provider.connected:
            raise self.skipTest("No Bloomberg connection")

    def test_futures_strategy(self):
        expected_value = 10317477.750000006
        expected_data_checksum = "88eb90dc28c7375204507ed2a112543955757f04"
        actual_end_value, actual_data_checksum = futures_strategy.run_strategy(self.data_provider)

        self.assertAlmostEqual(expected_value, actual_end_value, places=2)
        self.assertEqual(expected_data_checksum, actual_data_checksum)

    def test_simple_ma_strategy(self):
        expected_value = 898294.64
        expected_data_checksum = "0a29492c3a276286375f08c51a9733a37e60f81e"
        actual_end_value, actual_data_checksum = simple_ma_strategy.run_strategy(self.data_provider)

        self.assertAlmostEqual(expected_value, actual_end_value, places=2)
        self.assertEqual(expected_data_checksum, actual_data_checksum)

    def test_spx_with_stop_loss(self):
        expected_value = 1137843
        expected_data_checksum = "76bb3cb970068333d0d46b017871c7063dcd6fe2"
        actual_end_value, actual_data_checksum = spx_with_stop_loss.run_strategy(self.data_provider)

        self.assertAlmostEqual(expected_value, actual_end_value, delta=10)
        self.assertEqual(expected_data_checksum, actual_data_checksum)
