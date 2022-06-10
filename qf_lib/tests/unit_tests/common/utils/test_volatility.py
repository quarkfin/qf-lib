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

from pandas import date_range

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.common.utils.volatility.rolling_volatility import rolling_volatility
from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestVolatilityUtils(TestCase):
    def setUp(self):
        return_dates = date_range('1991-05-14', periods=7, freq='D')
        return_values = [0.5, 1, -0.75, 0.3333333333, 0.2, 0.5, -0.44444444]
        self.log_returns_tms = LogReturnsSeries(data=return_values, index=return_dates, dtype=float)

    def test_get_volatility(self):
        expected_volatility = 9.513791146776931
        actual_volatility = get_volatility(self.log_returns_tms, frequency=Frequency.DAILY)
        self.assertAlmostEqual(expected_volatility, actual_volatility)

    def test_rolling_volatility(self):
        dates = self.log_returns_tms.index[2::]
        values = [0.90138781886599728, 0.8832285053076373, 0.59074654587899456, 0.15030832509532852,
                  0.48257709858871728]
        expected_series = QFSeries(index=dates, data=values)

        actual_series = rolling_volatility(self.log_returns_tms, annualise=False, window_size=3)

        assert_series_equal(expected_series, actual_series)
