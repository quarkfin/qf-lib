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
from unittest import TestCase

from numpy import nan
from pandas import isnull, DatetimeIndex

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import TICKERS, FIELDS, DATES
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal, \
    assert_dataarrays_equal
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestDataProvidersHelpers(TestCase):

    def setUp(self) -> None:
        self.tickers = [DummyTicker("Dummy ticker")]
        self.fields = ["FIELD_1"]
        self.dates = [datetime(2022, 3, 1)]
        self.single_element_data_array = QFDataArray.create(dates=[datetime(2022, 3, 1)], tickers=self.tickers,
                                                            fields=self.fields, data=[[[17.0]]])
        self.empty_data_array = QFDataArray.create(dates=[datetime(2022, 3, 1)], tickers=self.tickers,
                                                   fields=self.fields, data=[[[nan]]])

    def test_normalize_data_array__single_date_single_ticker_single_field(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     True, True, True)
        self.assertEqual(normalized_data_array, 17.0)

    def test_normalize_data_array__single_date_single_ticker_single_field__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields, True, True, True)
        self.assertTrue(isnull(normalized_data_array))

    def test_normalize_data_array__single_date_single_ticker_multiple_fields(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     True, True, False)
        expected_result = QFSeries([17.0], index=self.fields)
        expected_result.name = self.tickers[0].as_string()
        expected_result.index.name = FIELDS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__single_date_single_ticker_multiple_fields__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     True, True, False)
        expected_result = QFSeries(index=self.fields, data=[nan])
        expected_result.name = self.tickers[0].as_string()
        expected_result.index.name = FIELDS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__single_date_multiple_tickers_single_field(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     True, False, True)
        expected_result = QFSeries([17.0], index=self.tickers)
        expected_result.name = "FIELD_1"
        expected_result.index.name = TICKERS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__single_date_multiple_tickers_single_field__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     True, False, True)
        expected_result = QFSeries(index=self.tickers, data=[nan])
        expected_result.name = "FIELD_1"
        expected_result.index.name = TICKERS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_single_ticker_single_field(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     False, True, True)
        expected_result = QFSeries([17.0], index=self.dates)
        expected_result.name = self.tickers[0].as_string()
        expected_result.index.name = DATES
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_single_ticker_single_field__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     False, True, True)
        expected_result = QFSeries(index=DatetimeIndex([], name=DATES))
        expected_result.name = self.tickers[0].as_string()
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__single_date_multiple_tickers_multiple_fields(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     True, False, False)
        expected_result = QFDataFrame([17.0], index=self.tickers, columns=self.fields)
        expected_result.index.name = TICKERS
        expected_result.columns.name = FIELDS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__single_date_multiple_tickers_multiple_fields__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     True, False, False)
        expected_result = QFDataFrame(index=self.tickers, columns=self.fields, data=[[nan]])
        expected_result.index.name = TICKERS
        expected_result.columns.name = FIELDS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_single_ticker_multiple_fields(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     False, True, False)
        expected_result = QFDataFrame([17.0], index=self.dates, columns=self.fields)
        expected_result.index.name = DATES
        expected_result.columns.name = FIELDS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_single_ticker_multiple_fields__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     False, True, False)
        expected_result = QFDataFrame(columns=self.fields, index=DatetimeIndex([], name=DATES))
        expected_result.columns.name = FIELDS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_multiple_tickers_single_field(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     False, False, True)
        expected_result = QFDataFrame([17.0], index=self.dates, columns=self.tickers)
        expected_result.index.name = DATES
        expected_result.columns.name = TICKERS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_multiple_tickers_single_field__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     False, False, True)
        expected_result = QFDataFrame(columns=self.tickers, index=DatetimeIndex([], name=DATES))
        expected_result.columns.name = TICKERS
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_multiple_tickers_multiple_fields(self):
        normalized_data_array = normalize_data_array(self.single_element_data_array, self.tickers, self.fields,
                                                     False, False, False)
        expected_result = QFDataArray.create(self.dates, self.tickers, self.fields, data=[[[17.0]]])
        self._assert_containers_equal(normalized_data_array, expected_result)

    def test_normalize_data_array__multiple_dates_multiple_tickers_multiple_fields__empty_container(self):
        normalized_data_array = normalize_data_array(self.empty_data_array, self.tickers, self.fields,
                                                     False, False, False)
        self.assertTrue(normalized_data_array.shape, (0, len(self.tickers), len(self.fields)))

    @staticmethod
    def _assert_containers_equal(expected_container, actual_container):
        if isinstance(expected_container, QFSeries):
            assert_series_equal(expected_container, actual_container)
        elif isinstance(expected_container, QFDataFrame):
            assert_dataframes_equal(expected_container, actual_container)
        elif isinstance(expected_container, QFDataArray):
            assert_dataarrays_equal(expected_container, actual_container)
