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

from numpy import array
from pandas import date_range

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.close_open_gap.close_open_gap import close_open_gap
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_lists_equal


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
