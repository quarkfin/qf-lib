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

import pandas as pd
import numpy as np
from qf_lib.common.utils.data_cleaner import DataCleaner
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal


class TestDataCleaner(TestCase):
    def setUp(self):
        self.test_dataframe = self._create_test_dataframe()
        self.test_benchmark = self._create_test_benchmark()
        self.data_cleaner = DataCleaner(self.test_dataframe)

    @classmethod
    def _create_test_dataframe(cls):
        values = [[np.nan, 0.0, 0.0, 0.0, 0.0],
                  [1.0, np.nan, 1.0, 1.0, 1.0],
                  [2.0, np.nan, np.nan, 2.0, 2.0],
                  [3.0, 3.0, 3.0, np.nan, 3.0],
                  [4.0, 4.0, 4.0, 4.0, 4.0],
                  [5.0, 5.0, 5.0, 5.0, 5.0]]

        index = pd.date_range(start='2015-01-01', periods=6)
        columns = ['a', 'b', 'c', 'd', 'e']
        dataframe = SimpleReturnsDataFrame(data=values, index=index, columns=columns)

        return dataframe

    @classmethod
    def _create_test_benchmark(cls):
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        index = pd.date_range(start='2015-01-02', periods=6)

        return SimpleReturnsSeries(data=values, index=index, name='Test prices')

    def test_proxy_using_values(self):
        expected_values = [[0.0, 0.0, 0.0, 0.0],
                           [1.0, 1.0, 1.0, 1.0],
                           [2.0, 0.0, 2.0, 2.0],
                           [3.0, 3.0, 0.0, 3.0],
                           [4.0, 4.0, 4.0, 4.0],
                           [5.0, 5.0, 5.0, 5.0]]
        expected_columns = ['a', 'c', 'd', 'e']
        expected_dates = self.test_dataframe.index.copy()
        expected_dataframe = SimpleReturnsDataFrame(data=expected_values, columns=expected_columns, index=expected_dates)
        self.data_cleaner.threshold = 0.2

        actual_dataframe = self.data_cleaner.proxy_using_value(proxy_value=0.0)

        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_proxy_using_regression(self):
        expected_values = [[np.nan, 0.0, 0.0, 0.0],
                           [1.0, 1.0, 1.0, 1.0],
                           [2.0, 2.0, 2.0, 2.0],
                           [3.0, 3.0, 3.0, 3.0],
                           [4.0, 4.0, 4.0, 4.0],
                           [5.0, 5.0, 5.0, 5.0]]
        expected_columns = ['a', 'c', 'd', 'e']
        expected_dates = self.test_dataframe.index.copy()
        expected_dataframe = SimpleReturnsDataFrame(data=expected_values, columns=expected_columns, index=expected_dates)
        self.data_cleaner.threshold = 0.2

        actual_dataframe = self.data_cleaner.proxy_using_regression(benchmark_tms=self.test_benchmark,
                                                                    columns_type=SimpleReturnsSeries)

        assert_dataframes_equal(expected_dataframe, actual_dataframe)
