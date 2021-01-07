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
from unittest.mock import Mock

from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.returns.sqn import sqn_for100trades, avg_nr_of_trades_per1y, sqn
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class TestSqnUtils(TestCase):
    def setUp(self):
        # Parameters defining start time, end time and r_multiply / arithmetic return of a trade
        trades_parameters = [
            [str_to_date("2015-01-03"), str_to_date("2015-01-10"), 0.1],
            [str_to_date("2015-02-01"), str_to_date("2015-02-10"), -0.05],
            [str_to_date("2015-03-01"), str_to_date("2015-03-30"), -0.05],
            [str_to_date("2015-04-01"), str_to_date("2015-04-30"), 0.1],
            [str_to_date("2015-05-01"), str_to_date("2015-05-08"), -0.05],
            [str_to_date("2015-06-01"), str_to_date("2015-06-23"), 0.1],
            [str_to_date("2015-07-01"), str_to_date("2015-07-30"), -0.05]
        ]

        self.trades = [
            Mock(start_time=params[0], end_time=params[1], percentage_pnl=params[2])
            for params in trades_parameters
        ]

    def test_sqn(self):
        expected_value = 0.178174161
        actual_return = sqn(SimpleReturnsSeries(t.percentage_pnl for t in self.trades))
        self.assertAlmostEqual(expected_value, actual_return, places=4)

    def test_sqn_100_trades(self):
        expected_value = 1.78174161
        actual_return = sqn_for100trades(SimpleReturnsSeries(t.percentage_pnl for t in self.trades))
        self.assertAlmostEqual(expected_value, actual_return, places=4)

    def test_avg_nr_of_trades_per1y(self):
        expected_value = 3.50
        actual_return = avg_nr_of_trades_per1y(SimpleReturnsSeries(t.percentage_pnl for t in self.trades),
                                               str_to_date("2015-01-01"), str_to_date("2016-12-31"))
        self.assertAlmostEqual(expected_value, actual_return, places=2)


if __name__ == '__main__':
    unittest.main()
