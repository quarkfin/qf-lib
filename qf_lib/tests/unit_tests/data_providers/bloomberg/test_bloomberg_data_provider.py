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
import random
import string
from unittest import TestCase
from unittest.mock import patch

from numpy import nan

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.helpers import grouper
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers import BloombergDataProvider
from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal
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

    def test_create_exchange_rate_ticker(self):
        result = self.bbg_provider.create_exchange_rate_ticker("PLN", "CHF")
        expected = BloombergTicker("PLNCHF Curncy", SecurityType.FX)
        self.assertEqual(result, expected)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe__single_page(self, get_mock):
        mocked_function, index_weights = self._mock_index_members_weights(n_elements=2999)
        get_mock.side_effect = mocked_function

        result = self.bbg_provider.get_tickers_universe(BloombergTicker('TPX Index'))
        expected = [BloombergTicker(f"{el['Index Member']} Equity") for el in index_weights]

        self.assertCountEqual(result, expected)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe__single_page_max_members_per_page(self, get_mock):
        mocked_function, index_weights = self._mock_index_members_weights(n_elements=3000)

        get_mock.side_effect = mocked_function
        result = self.bbg_provider.get_tickers_universe(BloombergTicker('TPX Index'))
        expected = [BloombergTicker(f"{el['Index Member']} Equity") for el in index_weights]
        self.assertCountEqual(result, expected)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe__multiple_pages(self, get_mock):
        mocked_function, index_weights = self._mock_index_members_weights(n_elements=11500)

        get_mock.side_effect = mocked_function
        result = self.bbg_provider.get_tickers_universe(BloombergTicker('TPX Index'))
        expected = [BloombergTicker(f"{el['Index Member']} Equity") for el in index_weights]
        self.assertCountEqual(result, expected)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe__incorrect_ticker(self, get_mock):
        get_mock.return_value = QFDataFrame.from_dict({'INDEX_MEMBERS_WEIGHTS': {BloombergTicker('TPXa Index'): nan}})
        result = self.bbg_provider.get_tickers_universe(BloombergTicker('TPX Index'))
        expected = []
        self.assertCountEqual(result, expected)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe_with_weights__single_page(self, get_mock):
        mocked_function, index_weights = self._mock_index_members_weights(n_elements=2999)
        get_mock.side_effect = mocked_function

        result = self.bbg_provider.get_tickers_universe_with_weights(BloombergTicker('TPX Index'))
        expected = QFSeries(data=[el['Weight'] for el in index_weights],
                            index=[BloombergTicker(f"{el['Index Member']} Equity") for el in index_weights])

        assert_series_equal(result, expected, check_names=False)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe_with_weights__single_page_max(self, get_mock):
        mocked_function, index_weights = self._mock_index_members_weights(n_elements=3000)
        get_mock.side_effect = mocked_function

        result = self.bbg_provider.get_tickers_universe_with_weights(BloombergTicker('TPX Index'))
        expected = QFSeries(data=[el['Weight'] for el in index_weights],
                            index=[BloombergTicker(f"{el['Index Member']} Equity") for el in index_weights])

        assert_series_equal(result, expected, check_names=False)

    @patch.object(ReferenceDataProvider, "get")
    def test_get_tickers_universe_with_weights__multiple_pages(self, get_mock):
        mocked_function, index_weights = self._mock_index_members_weights(n_elements=4500)
        get_mock.side_effect = mocked_function

        result = self.bbg_provider.get_tickers_universe_with_weights(BloombergTicker('TPX Index'))
        expected = QFSeries(data=[el['Weight'] for el in index_weights],
                            index=[BloombergTicker(f"{el['Index Member']} Equity") for el in index_weights])

        assert_series_equal(result, expected, check_names=False)

    def _mock_index_members_weights(self, n_elements: int):
        """ Create randomized elements for the index, for the test Weights don't need to sum up to 1.0. """
        MAX_MEMBERS_PER_PAGE = 3000
        index_weights = [{'Index Member': ''.join(random.choices(string.ascii_uppercase, k=3)),
                          'Weight': random.uniform(0, 1)} for _ in range(n_elements)]

        weights_iter = iter(grouper(MAX_MEMBERS_PER_PAGE, index_weights))

        def get_next_weights_page(*args, **kwargs):
            try:
                return QFDataFrame.from_dict({'INDEX_MEMBERS_WEIGHTS': {
                    BloombergTicker('TPX Index'): next(weights_iter)}})
            except StopIteration:
                return QFDataFrame.from_dict({'INDEX_MEMBERS_WEIGHTS': {
                    BloombergTicker('TPX Index'): []}})

        return get_next_weights_page, index_weights
