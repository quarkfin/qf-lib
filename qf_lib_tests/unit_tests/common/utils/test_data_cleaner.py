from unittest import TestCase

import pandas as pd

from qf_lib.common.utils.data_cleaner import DataCleaner
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.testing_tools.containers_comparison import assert_dataframes_equal


class TestDataCleaner(TestCase):
    def setUp(self):
        self.test_dataframe = self._create_test_dataframe()
        self.test_benchmark = self._create_test_benchmark()
        self.data_cleaner = DataCleaner(self.test_dataframe)

    @classmethod
    def _create_test_dataframe(cls):
        values = [[pd.np.nan, 0.0,       0.0,       0.0,       0.0],
                  [1.0,       pd.np.nan, 1.0,       1.0,       1.0],
                  [2.0,       pd.np.nan, pd.np.nan, 2.0,       2.0],
                  [3.0,       3.0,       3.0,       pd.np.nan, 3.0],
                  [4.0,       4.0,       4.0,       4.0,       4.0],
                  [5.0,       5.0,       5.0,       5.0,       5.0]]

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
        expected_values = [[pd.np.nan, 0.0, 0.0, 0.0],
                           [1.0,       1.0, 1.0, 1.0],
                           [2.0,       2.0, 2.0, 2.0],
                           [3.0,       3.0, 3.0, 3.0],
                           [4.0,       4.0, 4.0, 4.0],
                           [5.0,       5.0, 5.0, 5.0]]
        expected_columns = ['a', 'c', 'd', 'e']
        expected_dates = self.test_dataframe.index.copy()
        expected_dataframe = SimpleReturnsDataFrame(data=expected_values, columns=expected_columns, index=expected_dates)
        self.data_cleaner.threshold = 0.2

        actual_dataframe = self.data_cleaner.proxy_using_regression(benchmark_tms=self.test_benchmark,
                                                                    columns_type=SimpleReturnsSeries)

        assert_dataframes_equal(expected_dataframe, actual_dataframe)
