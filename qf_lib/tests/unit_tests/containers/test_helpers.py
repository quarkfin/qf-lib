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
from numpy import nan, dtype
from xarray.testing import assert_equal

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.helpers import compute_container_hash
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.returns_series import ReturnsSeries
from qf_lib.data_providers.helpers import tickers_dict_to_data_array


class TestSeries(TestCase):
    def setUp(self):
        self.index = pd.date_range(start='2017-01-01', end='2017-12-31', freq='BMS')

    def test_compute_container_hash__series(self):
        list_of_data = list(range(200))
        qfseries_1 = QFSeries(data=list_of_data)
        qfseries_2 = QFSeries(data=list_of_data)
        returns_series = ReturnsSeries(data=list_of_data)
        prices_series = PricesSeries(data=list_of_data)

        self.assertEqual(compute_container_hash(qfseries_1), compute_container_hash(qfseries_2))
        self.assertEqual(compute_container_hash(qfseries_1), compute_container_hash(returns_series))
        self.assertEqual(compute_container_hash(qfseries_1), compute_container_hash(prices_series))

    def test_compute_container_hash__df(self):
        """
        The order of the columns matters and changes the hash of the data frame.
        """
        column_1 = [1, 2, 3]
        column_2 = [4, 5, 6]

        df_1 = QFDataFrame(data={"A": column_1, "B": column_2}, columns=["A", "B"])
        df_2 = QFDataFrame(data={"A": column_1, "B": column_2}, columns=["B", "A"])

        self.assertNotEqual(compute_container_hash(df_1), compute_container_hash(df_2))
        self.assertEqual(compute_container_hash(df_1.sort_index(axis=1)),
                         compute_container_hash(df_2.sort_index(axis=1)))

    def test_compute_container_hash__data_array(self):
        ticker_1 = BloombergTicker("Example 1")
        ticker_2 = BloombergTicker("Example 2")

        prices_df_1 = QFDataFrame(data={PriceField.Close: [1, 2, 3], PriceField.Open: [4, 5, 6]})
        prices_df_2 = QFDataFrame(data={PriceField.Close: [5, 7, 8]})

        data_array_1 = tickers_dict_to_data_array({
            ticker_1: prices_df_1,
            ticker_2: prices_df_2
        }, [ticker_1, ticker_2], [PriceField.Open, PriceField.Close])

        data_array_2 = tickers_dict_to_data_array({
            ticker_1: prices_df_1,
            ticker_2: prices_df_2,
        }, [ticker_1, ticker_2], [PriceField.Open, PriceField.Close])

        data_array_3 = tickers_dict_to_data_array({
            ticker_2: prices_df_2,
            ticker_1: prices_df_1,
        }, [ticker_1, ticker_2], [PriceField.Open, PriceField.Close])

        self.assertEqual(compute_container_hash(data_array_1), compute_container_hash(data_array_2))
        self.assertEqual(compute_container_hash(data_array_1), compute_container_hash(data_array_3))

    def test_tickers_dict_to_data_array(self):
        ticker_1 = BloombergTicker("Example 1")
        ticker_2 = BloombergTicker("Example 2")
        fields = [PriceField.Open, PriceField.Close]
        index = self.index[:3]
        data = [[[4., 1.], [nan, 5.]],
                [[5., 2.], [nan, 7.]],
                [[6., 3.], [nan, 8.]]]

        prices_df_1 = QFDataFrame(data={PriceField.Close: [1., 2., 3.], PriceField.Open: [4., 5., 6.]}, index=index)
        prices_df_2 = QFDataFrame(data={PriceField.Close: [5., 7., 8.]}, index=index)

        data_array = tickers_dict_to_data_array({
            ticker_1: prices_df_1,
            ticker_2: prices_df_2
        }, [ticker_1, ticker_2], fields)

        self.assertEqual(dtype("float64"), data_array.dtype)

        expected_data_array = QFDataArray.create(index, [ticker_1, ticker_2], fields, data)
        assert_equal(data_array, expected_data_array)

    def test_tickers_dict_to_data_array_single_field(self):
        ticker_1 = BloombergTicker("Example 1")
        ticker_2 = BloombergTicker("Example 2")
        fields = PriceField.Open
        index = self.index[:3]

        prices_df_1 = QFDataFrame(data={PriceField.Close: [1., 2., 3.], PriceField.Open: [4., 5., 6.]}, index=index)
        prices_df_2 = QFDataFrame(data={PriceField.Close: [5., 7., 8.], PriceField.Low: [5., 5., 5.]}, index=index)

        data_array = tickers_dict_to_data_array({
            ticker_1: prices_df_1,
            ticker_2: prices_df_2
        }, [ticker_1, ticker_2], fields)

        self.assertEqual(dtype("float64"), data_array.dtype)

        data = [[[4.], [nan]],
                [[5.], [nan]],
                [[6.], [nan]]]

        expected_data_array = QFDataArray.create(index, [ticker_1, ticker_2], [fields], data)
        assert_equal(data_array, expected_data_array)

    def test_tickers_dict_to_data_array_single_field_single_ticker(self):
        ticker_1 = BloombergTicker("Example 1")
        ticker_2 = BloombergTicker("Example 2")
        fields = "PX_LAST"
        index = self.index[:3]

        prices_df_1 = QFDataFrame(data={PriceField.Close: [1., 2., 3.], "PX_LAST": [4., 5., 6.]}, index=index)
        prices_df_2 = QFDataFrame(data={PriceField.Close: [5., 7., 8.], PriceField.Low: [5., 5., 5.]}, index=index)

        data_array = tickers_dict_to_data_array({
            ticker_1: prices_df_1,
            ticker_2: prices_df_2
        }, ticker_1, fields)

        self.assertEqual(dtype("float64"), data_array.dtype)

        data = [[[4.]],
                [[5.]],
                [[6.]]]

        expected_data_array = QFDataArray.create(index, [ticker_1], [fields], data)
        assert_equal(data_array, expected_data_array)


if __name__ == '__main__':
    unittest.main()
