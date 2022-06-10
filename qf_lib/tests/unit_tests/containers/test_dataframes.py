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
from unittest import TestCase

import pandas as pd
from numpy import dtype

from qf_lib.containers.dataframe.log_returns_dataframe import LogReturnsDataFrame
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal, assert_series_equal


class TestDataFrames(TestCase):
    def setUp(self):
        self.dates = pd.date_range(start='2015-05-13', periods=5)
        self.column_names = ['a', 'b', 'c', 'd', 'e']

        self.prices_values = [[1., 1., 1., 1, 1.],
                              [2., 2., 2., 2., 2.],
                              [3., 3., 3., 3., 3.],
                              [4., 4., 4., 4., 4.],
                              [5., 5., 5., 5., 5.]]
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

    def test_prices_dataframe_dtypes(self):
        dtypes = self.test_prices_df.dtypes
        self.assertEqual({dtype("float64")}, set(dtypes))

    def test_log_returns_dataframe_dtypes(self):
        dtypes = self.test_log_returns_df.dtypes
        self.assertEqual({dtype("float64")}, set(dtypes))

    def test_simple_returns_dataframe_dtypes(self):
        dtypes = self.test_simple_returns_df.dtypes
        self.assertEqual({dtype("float64")}, set(dtypes))

    def test_prices_to_log_returns(self):
        expected_dataframe = self.test_log_returns_df

        actual_dataframe = self.test_prices_df.to_log_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_simple_to_log_returns(self):
        expected_dataframe = self.test_log_returns_df

        actual_dataframe = self.test_simple_returns_df.to_log_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_log_to_log_returns(self):
        expected_dataframe = self.test_log_returns_df

        actual_dataframe = self.test_log_returns_df.to_log_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_log_to_simple_returns(self):
        expected_dataframe = self.test_simple_returns_df

        actual_dataframe = self.test_log_returns_df.to_simple_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_simple_to_simple_returns(self):
        expected_dataframe = self.test_simple_returns_df

        actual_dataframe = self.test_simple_returns_df.to_simple_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_prices_to_simple_returns(self):
        expected_dataframe = self.test_simple_returns_df

        actual_dataframe = self.test_prices_df.to_simple_returns()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_log_returns_to_prices(self):
        expected_dataframe = self.test_prices_df

        actual_dataframe = self.test_log_returns_df.to_prices()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_simple_returns_to_prices(self):
        expected_dataframe = self.test_prices_df

        actual_dataframe = self.test_simple_returns_df.to_prices()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_prices_to_prices(self):
        expected_dataframe = self.test_prices_df

        actual_dataframe = self.test_prices_df.to_prices()
        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_min_max_normalized(self):
        normalized_prices = [[0.00, 0.00, 0.00, 0.00, 0.00],
                             [0.25, 0.25, 0.25, 0.25, 0.25],
                             [0.50, 0.50, 0.50, 0.50, 0.50],
                             [0.75, 0.75, 0.75, 0.75, 0.75],
                             [1.00, 1.00, 1.00, 1.00, 1.00]]
        expected_dataframe = PricesDataFrame(data=normalized_prices, index=self.dates, columns=self.column_names)

        actual_dataframe = self.test_prices_df.min_max_normalized()

        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_exponential_average(self):
        smoothed_values = [[1.000000, 1.000000, 1.000000, 1.000000, 1.000000],
                           [1.940000, 1.940000, 1.940000, 1.940000, 1.940000],
                           [2.936400, 2.936400, 2.936400, 2.936400, 2.936400],
                           [3.936184, 3.936184, 3.936184, 3.936184, 3.936184],
                           [4.936171, 4.936171, 4.936171, 4.936171, 4.936171]]
        expected_dataframe = PricesDataFrame(data=smoothed_values, index=self.dates, columns=self.column_names)

        actual_dataframe = self.test_prices_df.exponential_average()

        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

    def test_aggregate_by_year(self):
        dates = pd.DatetimeIndex(['2015-06-01', '2015-12-30', '2016-01-01', '2016-05-01'])
        test_dataframe = SimpleReturnsDataFrame(data=self.simple_returns_values, index=dates)

        expected_aggregated_rets = [[2.000000, 2.000000, 2.000000, 2.000000, 2.000000],
                                    [0.666666, 0.666666, 0.666666, 0.666666, 0.666666]]
        expected_dataframe = SimpleReturnsDataFrame(data=expected_aggregated_rets,
                                                    index=pd.DatetimeIndex(['2015-12-31', '2016-12-31']))

        actual_dataframe = test_dataframe.aggregate_by_year()

        assert_dataframes_equal(expected_dataframe, actual_dataframe)
        self.assertEqual({dtype("float64")}, set(actual_dataframe.dtypes))

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
        self.assertEqual(dtype("float64"), actual_result.dtypes)

    def test_total_cumulative_return(self):
        actual_result = self.test_prices_df.total_cumulative_return()
        expected_result = PricesSeries(index=self.test_prices_df.columns, data=[4.0, 4.0, 4.0, 4.0, 4.0])
        assert_series_equal(expected_result, actual_result)
        self.assertEqual(dtype("float64"), actual_result.dtypes)

    def test_stats_functions(self):
        qf_df = QFDataFrame(data=self.prices_values, index=self.dates, columns=self.column_names)
        max_qf_df = qf_df.max()
        expected_max = QFSeries([5, 5, 5, 5, 5], index=['a', 'b', 'c', 'd', 'e'])

        self.assertEqual(type(max_qf_df), QFSeries)
        assert_series_equal(max_qf_df, expected_max)
        self.assertEqual(dtype("float64"), max_qf_df.dtypes)

    def test_squeeze(self):
        qf_df = QFDataFrame(data=self.prices_values, index=self.dates, columns=self.column_names)
        self.assertEqual(type(qf_df[['a']]), QFDataFrame)
        self.assertEqual({dtype("float64")}, set(qf_df[['a']].dtypes))

        self.assertEqual(type(qf_df[['a']].squeeze()), QFSeries)
        self.assertEqual(dtype("float64"), qf_df[['a']].squeeze().dtypes)

        self.assertEqual(type(qf_df[['a', 'b']].squeeze()), QFDataFrame)
        self.assertEqual({dtype("float64")}, set(qf_df[['a', 'b']].squeeze().dtypes))

        self.assertEqual(type(qf_df.iloc[[0]]), QFDataFrame)
        self.assertEqual({dtype("float64")}, set(qf_df.iloc[[0]].dtypes))

        self.assertEqual(type(qf_df.iloc[[0]].squeeze()), QFSeries)
        self.assertEqual("float64", qf_df.iloc[[0]].squeeze().dtypes)

    def test_concat(self):
        full_df = QFDataFrame(data=self.prices_values, index=self.dates, columns=self.column_names)

        # Concatenate along index (axis = 0)
        number_of_rows = len(full_df)
        half_df = full_df.iloc[:number_of_rows//2]
        second_half_df = full_df.iloc[number_of_rows//2:]
        concatenated_df = pd.concat([half_df, second_half_df])

        self.assertEqual(type(concatenated_df), QFDataFrame)
        self.assertEqual({dtype("float64")}, set(concatenated_df.dtypes))
        assert_dataframes_equal(concatenated_df, full_df)

        # Concatenate along columns (axis = 1)
        number_of_columns = full_df.num_of_columns
        half_df = full_df.loc[:, full_df.columns[:number_of_columns//2]]
        second_half_df = full_df.loc[:, full_df.columns[number_of_columns//2:]]
        concatenated_df = pd.concat([half_df, second_half_df], axis=1)

        self.assertEqual(type(concatenated_df), QFDataFrame)
        self.assertEqual({dtype("float64")}, set(concatenated_df.dtypes))
        assert_dataframes_equal(concatenated_df, full_df)

    def test_concat_series(self):
        index = [1, 2, 3]
        series_1 = QFSeries(data=[17., 15., 16.], index=index)
        series_2 = QFSeries(data=[18., 19., 20.], index=index)

        df = pd.concat([series_1, series_2], axis=1)
        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual({s.dtypes for s in [series_1, series_2]}, set(df.dtypes))

        series = pd.concat([series_1, series_2], axis=0)
        self.assertEqual(type(series), QFSeries)
        self.assertEqual("float64", series.dtypes)
        self.assertEqual({s.dtypes for s in [series_1, series_2]}, {series.dtypes})


if __name__ == '__main__':
    unittest.main()
