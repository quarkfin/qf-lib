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

import numpy as np
import pandas as pd
from pandas import date_range
from xarray.testing import assert_equal

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal


class TestQFDataArrayAsOf(TestCase):
    def setUp(self):
        self.dates = pd.date_range(start='2018-02-04', periods=3)
        self.spx_ticker = BloombergTicker('SPX Index')
        self.spy_ticker = BloombergTicker('SPY US Equity')
        self.tickers = [self.spx_ticker, self.spy_ticker]
        self.fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]

        self.qf_data_array = self._get_sample_data_array(self.dates, self.tickers, self.fields)
        self.qf_data_array.loc[str_to_date('2018-02-04'), self.spy_ticker, PriceField.Open] = np.nan
        self.qf_data_array.loc[str_to_date('2018-02-06'), self.spy_ticker, :] = np.nan
        # 2018-02-04
        #      O    H    L    C
        # SPX [0,   1,   2,   3]
        # SPY [nan, 5,   6,   7]
        #
        # 2018-02-05
        #      O    H    L    C
        # SPX [8,  9,  10, 11]
        # SPY [12, 13, 14, 15]
        #
        # 2018-02-06
        #      O   H   L   C
        # SPX [16, 17, 18, 19]
        # SPY [nan, nan, nan, nan]

    @classmethod
    def _get_sample_data_array(cls, dates, tickers, fields):
        num_of_dates = len(dates)
        num_of_tickers = len(tickers)
        num_of_fields = len(fields)

        sample_data = [float(i) for i in range(num_of_dates * num_of_tickers * num_of_fields)]
        sample_3d_data = np.reshape(sample_data, (num_of_dates, num_of_tickers, num_of_fields))

        sample_data_array = QFDataArray.create(dates, tickers, fields, sample_3d_data)
        return sample_data_array

    def test_asof_nans_when_no_data_available(self):
        actual_result = self.qf_data_array.asof(str_to_date('2018-02-02'))
        expected_result = QFDataFrame(
            index=self.qf_data_array.tickers.to_index(),
            columns=self.qf_data_array.fields.to_index()
        )
        assert_dataframes_equal(expected_result, actual_result)

    def test_asof_multiple_dates(self):
        actual_result = self.qf_data_array.asof([str_to_date('2018-02-05'), str_to_date('2018-02-04')])
        expected_result = QFDataFrame(
            index=self.qf_data_array.tickers.to_index(),
            columns=self.qf_data_array.fields.to_index(),
            data=[
                [8, 9, 10, 11],
                [np.nan, np.nan, np.nan, np.nan]
            ]
        )
        assert_dataframes_equal(expected_result, actual_result)

    def test_asof_multiple_dates_gaps_at_the_end(self):
        actual_result = self.qf_data_array.asof(str_to_date('2018-02-06'))
        expected_result = QFDataFrame(
            index=self.qf_data_array.tickers.to_index(),
            columns=self.qf_data_array.fields.to_index(),
            data=[
                [16, 17, 18, 19],
                [12, 13, 14, 15]
            ]
        )
        assert_dataframes_equal(expected_result, actual_result)

    def test_number_of_ticers_equal_to_number_of_dates(self):
        with self.assertRaises(ValueError):
            self.qf_data_array.asof([str_to_date('2018-02-05')])

    def test_data_arrays_concat_on_dates(self):
        ticker_1 = BloombergTicker("Example 1")
        ticker_2 = BloombergTicker("Example 2")
        fields = [PriceField.Open, PriceField.Close]
        index = date_range(start=str_to_date("2017-01-01"), periods=5, freq="D")

        index_1 = index[:3]
        data_1 = [[[4., 1.], [np.nan, 5.]],
                  [[5., 2.], [np.nan, 7.]],
                  [[6., 3.], [np.nan, 8.]]]

        data_array_1 = QFDataArray.create(index_1, [ticker_1, ticker_2], fields, data_1)
        self.assertEqual(np.dtype("float64"), data_array_1.dtype)

        index_2 = index[3:]
        data_2 = [[[7., 1.], [np.nan, 10.]],
                  [[8., 2.], [np.nan, 14.]]]

        data_array_2 = QFDataArray.create(index_2, [ticker_1, ticker_2], fields, data_2)
        self.assertEqual(np.dtype("float64"), data_array_2.dtype)

        data = [[[4., 1.], [np.nan, 5.]],
                [[5., 2.], [np.nan, 7.]],
                [[6., 3.], [np.nan, 8.]],
                [[7., 1.], [np.nan, 10.]],
                [[8., 2.], [np.nan, 14.]]]
        expected_data_array = QFDataArray.create(index, [ticker_1, ticker_2], fields, data)
        self.assertEqual(np.dtype("float64"), expected_data_array.dtype)

        concatenated_data_array = QFDataArray.concat([data_array_1, data_array_2], dim=DATES)
        self.assertEqual(np.dtype("float64"), concatenated_data_array.dtype)

        assert_equal(expected_data_array, concatenated_data_array)

    def test_data_arrays_concat_on_tickers(self):
        ticker_1 = BloombergTicker("Example 1")
        ticker_2 = BloombergTicker("Example 2")
        fields = [PriceField.Open, PriceField.Close]
        index = date_range(start=str_to_date("2017-01-01"), periods=5, freq="D")

        index_1 = index[:3]
        data_1 = [[[4., 1.]],
                  [[5., 2.]],
                  [[6., 3.]]]

        data_array_1 = QFDataArray.create(index_1, [ticker_1], fields, data_1)
        self.assertEqual(np.dtype("float64"), data_array_1.dtype)

        index_2 = index[3:]
        data_2 = [[[np.nan, 10.]],
                  [[np.nan, 14.]]]

        data_array_2 = QFDataArray.create(index_2, [ticker_2], fields, data_2)
        self.assertEqual(np.dtype("float64"), data_array_2.dtype)

        data = [[[4., 1.], [np.nan, np.nan]],
                [[5., 2.], [np.nan, np.nan]],
                [[6., 3.], [np.nan, np.nan]],
                [[np.nan, np.nan], [np.nan, 10.]],
                [[np.nan, np.nan], [np.nan, 14.]]]
        expected_data_array = QFDataArray.create(index, [ticker_1, ticker_2], fields, data)
        self.assertEqual(np.dtype("float64"), expected_data_array.dtype)

        concatenated_data_array = QFDataArray.concat([data_array_1, data_array_2], dim=TICKERS)
        self.assertEqual(np.dtype("float64"), concatenated_data_array.dtype)

        assert_equal(expected_data_array, concatenated_data_array)


if __name__ == '__main__':
    unittest.main()
