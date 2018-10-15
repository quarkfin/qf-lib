from unittest import TestCase

from numpy import array
from pandas import date_range

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.testing_tools.containers_comparison import assert_lists_equal
from scripts.analysis.ensamble_avg_vs_time_avg.close_open_gap import close_open_gap


class TestCloseOpenGapUtils(TestCase):
    def setUp(self):
        self.tms = date_range('1991-05-14', periods=6, freq='D')
        open = [100, 100, 100, 101, 101, 102]
        close = [100, 100, 100, 101, 101, 102]

        data_2d = array([open, close]).transpose()
        self.prices_df = PricesDataFrame(data=data_2d, index=self.tms, columns=[PriceField.Open, PriceField.Close])

    def test_open_close_gap(self):
        expected_values = [1.00, 1.00, 1.00, 1.01, 1.01, 1.02]
        actual_values = close_open_gap(self.prices_df)
        assert_lists_equal(expected_values, actual_values)
