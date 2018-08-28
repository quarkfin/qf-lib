import unittest
from unittest import TestCase

import numpy as np
import pandas as pd

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.testing_tools.containers_comparison import assert_dataframes_equal


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
        expected_result = pd.DataFrame(
            index=self.qf_data_array.tickers.to_index(),
            columns=self.qf_data_array.fields.to_index()
        )
        assert_dataframes_equal(expected_result, actual_result)

    def test_asof_multiple_dates(self):
        actual_result = self.qf_data_array.asof([str_to_date('2018-02-05'), str_to_date('2018-02-04')])
        expected_result = pd.DataFrame(
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
        expected_result = pd.DataFrame(
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


if __name__ == '__main__':
    unittest.main()
