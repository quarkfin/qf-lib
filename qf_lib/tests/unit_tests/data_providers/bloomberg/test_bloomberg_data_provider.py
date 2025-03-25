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
from unittest import TestCase
from unittest.mock import patch

from numpy import nan

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers import BloombergDataProvider
from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider
from qf_lib.tests.unit_tests.config.test_settings import get_test_settings


class TestBloombergDataProvider(TestCase):

    @patch('qf_lib.data_providers.bloomberg.bloomberg_data_provider.blpapi')
    def setUp(self, blpapi_mock) -> None:
        self.bbg_provider = BloombergDataProvider(get_test_settings())

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tabular_data__incorrect_field(self, get_mock):
        get_mock.return_value = QFDataFrame.from_dict({'PX_LAST': {BloombergTicker('TPX Index'): 2797.52}})
        with self.assertRaises(ValueError):
            self.bbg_provider.get_tabular_data(BloombergTicker('TPX Index'), "PX_LAST")

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tabular_data(self, get_mock):
        get_mock.return_value = QFDataFrame.from_dict({'INDEX_MEMBERS_WEIGHTS': {
            BloombergTicker('TPX Index'): [{'Index Member': 'A US', 'Weight': 0.05},
                                           {'Index Member': 'B US', 'Weight': 0.03}, ]}})

        result = self.bbg_provider.get_tabular_data(BloombergTicker('TPX Index'), "INDEX_MEMBERS_WEIGHTS")
        expected = [{"Index Member": "A US", "Weight": 0.05}, {"Index Member": "B US", "Weight": 0.03}]
        self.assertCountEqual(result, expected)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tabular_data__incorrect_ticker(self, get_mock):
        get_mock.return_value = QFDataFrame.from_dict({'INDEX_MEMBERS_WEIGHTS': {BloombergTicker('TPXa Index'): nan}})
        result = self.bbg_provider.get_tabular_data(BloombergTicker('TPX Index'), "PX_LAST")
        expected = []
        self.assertCountEqual(result, expected)
