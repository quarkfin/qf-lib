import unittest
from unittest import TestCase

import pandas as pd

from qf_lib.containers.dataframe.log_returns_dataframe import LogReturnsDataFrame
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.testing_tools.containers_comparison import assert_dataframes_equal, assert_series_equal


class TestDataFrames(TestCase):
    def setUp(self):
        self.dates = pd.date_range(start='2015-05-13', periods=5)
        self.column_names = ['a', 'b', 'c', 'd', 'e']

        self.prices_values = [[1, 1, 1, 1, 1],
                              [2, 2, 2, 2, 2],
                              [3, 3, 3, 3, 3],
                              [4, 4, 4, 4, 4],
                              [5, 5, 5, 5, 5]]
        self.test_prices_df = PricesDataFrame(data=self.prices_values, index=self.dates, columns=self.column_names)

        self.log_returns_values = [[0.693147, 0.693147, 0.693147, 0.693147, 0.693147],
                                   [0.405465, 0.405465, 0.405465, 0.405465, 0.405465],
                                   [0.287682, 0.287682, 0.287682, 0.287682, 0.287682],
                                   [0.223144, 0.223144, 0.223144, 0.223144, 0.223144]]
        self.test_log_returns_df = LogReturnsDataFrame(data=self.log_returns_values, index=self.dates[1:],
                                                       columns=self.column_names)

        self.simple_returns_values = [[1.000000, 1.000000, 1.000000, 1.000000, 1.000000],
                                      [0.500000, 0.500000, 0.500000, 0.500000, 0.500000],
                                      [0.333333, 0.333333, 0.333333, 0.333333, 0.333333],
                                      [0.250000, 0.250000, 0.250000, 0.250000, 0.250000]]
        self.test_simple_returns_df = SimpleReturnsDataFrame(data=self.simple_returns_values, index=self.dates[1:],
                                                             columns=self.column_names)

    def test_num_of_columns(self):
        self.assertEqual(self.test_prices_df.num_of_columns, 5)

    def test_prices_to_log_returns(self):
        expected_dataframe = self.test_log_returns_df

        actual_dataframe = self.test_prices_df.to_log_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_simple_to_log_returns(self):
        expected_dataframe = self.test_log_returns_df

        actual_dataframe = self.test_simple_returns_df.to_log_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_log_to_log_returns(self):
        expected_dataframe = self.test_log_returns_df

        actual_dataframe = self.test_log_returns_df.to_log_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_log_to_simple_returns(self):
        expected_dataframe = self.test_simple_returns_df

        actual_dataframe = self.test_log_returns_df.to_simple_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_simple_to_simple_returns(self):
        expected_dataframe = self.test_simple_returns_df

        actual_dataframe = self.test_simple_returns_df.to_simple_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_prices_to_simple_returns(self):
        expected_dataframe = self.test_simple_returns_df

        actual_dataframe = self.test_prices_df.to_simple_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_log_returns_to_prices(self):
        expected_dataframe = self.test_prices_df

        actual_dataframe = self.test_log_returns_df.to_prices()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_simple_returns_to_prices(self):
        expected_dataframe = self.test_prices_df

        actual_dataframe = self.test_simple_returns_df.to_prices()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_prices_to_prices(self):
        expected_dataframe = self.test_prices_df

        actual_dataframe = self.test_prices_df.to_prices()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_min_max_normalized(self):
        normalized_prices = [[0.00, 0.00, 0.00, 0.00, 0.00],
                             [0.25, 0.25, 0.25, 0.25, 0.25],
                             [0.50, 0.50, 0.50, 0.50, 0.50],
                             [0.75, 0.75, 0.75, 0.75, 0.75],
                             [1.00, 1.00, 1.00, 1.00, 1.00]]
        expected_dataframe = PricesDataFrame(data=normalized_prices, index=self.dates, columns=self.column_names)

        actual_dataframe = self.test_prices_df.min_max_normalized()

        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_exponential_average(self):
        smoothed_values = [[1.000000, 1.000000, 1.000000, 1.000000, 1.000000],
                           [1.940000, 1.940000, 1.940000, 1.940000, 1.940000],
                           [2.936400, 2.936400, 2.936400, 2.936400, 2.936400],
                           [3.936184, 3.936184, 3.936184, 3.936184, 3.936184],
                           [4.936171, 4.936171, 4.936171, 4.936171, 4.936171]]
        expected_dataframe = PricesDataFrame(data=smoothed_values, index=self.dates, columns=self.column_names)

        actual_dataframe = self.test_prices_df.exponential_average()

        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_aggregate_by_year(self):
        dates = pd.DatetimeIndex(['2015-06-01', '2015-12-30', '2016-01-01', '2016-05-01'])
        test_dataframe = SimpleReturnsDataFrame(data=self.simple_returns_values, index=dates)

        expected_aggregated_rets = [[2.000000, 2.000000, 2.000000, 2.000000, 2.000000],
                                    [0.666666, 0.666666, 0.666666, 0.666666, 0.666666]]
        expected_dataframe = SimpleReturnsDataFrame(data=expected_aggregated_rets,
                                                    index=pd.DatetimeIndex(['2015-12-31', '2016-12-31']))

        actual_dataframe = test_dataframe.aggregate_by_year()

        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_rolling_time_window(self):
        actual_result = self.test_prices_df.rolling_time_window(window_length=2, step=1, func=lambda x: x.mean())
        expected_values = [[1.5, 1.5, 1.5, 1.5, 1.5],
                           [2.5, 2.5, 2.5, 2.5, 2.5],
                           [3.5, 3.5, 3.5, 3.5, 3.5],
                           [4.5, 4.5, 4.5, 4.5, 4.5]]
        expected_index = self.test_prices_df.index[-4:].copy(deep=True)
        expected_columns = ['a', 'b', 'c', 'd', 'e']
        expected_result = QFDataFrame(expected_values, expected_index, expected_columns)
        assert_dataframes_equal(expected_result, actual_result, absolute_tolerance=1e-20)

        actual_result = self.test_prices_df.rolling_time_window(window_length=2, step=1, func=lambda x: x.mean().mean())
        expected_values = [1.5, 2.5, 3.5, 4.5]
        expected_index = self.test_prices_df.index[-4:].copy(deep=True)
        expected_result = QFSeries(expected_values, expected_index)
        assert_series_equal(expected_result, actual_result, absolute_tolerance=1e-20)

    def test_total_cumulative_return(self):
        actual_result = self.test_prices_df.total_cumulative_return()
        expected_result = pd.Series(index=self.test_prices_df.columns, data=[4.0, 4.0, 4.0, 4.0, 4.0])
        assert_series_equal(expected_result, actual_result)


if __name__ == '__main__':
    unittest.main()
