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

from pandas import date_range, DatetimeIndex

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.ratios.omega_ratio import omega_ratio
from qf_lib.common.utils.returns.annualise_total_return import annualise_total_return
from qf_lib.common.utils.returns.avg_drawdown import avg_drawdown
from qf_lib.common.utils.returns.avg_drawdown_duration import avg_drawdown_duration
from qf_lib.common.utils.returns.beta_and_alpha import beta_and_alpha
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.returns.cvar import cvar
from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.common.utils.returns.list_of_max_drawdowns import list_of_max_drawdowns
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.common.utils.returns.tail_events import tail_events
from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_lists_equal


class TestReturnsUtils(TestCase):
    def setUp(self):
        self.return_dates = date_range('2015-01-01', periods=20, freq='D')
        prices_values = [100, 101, 103.02, 106.1106, 108.232812, 109.31514012, 109.31514012, 108.2219887188,
                         106.057548944424, 107.118124433868, 110.331668166884, 115.848251575229, 120.482181638238,
                         124.096647087385, 126.578580029132, 127.844365829424, 127.844365829424, 129.1228094877180,
                         132.9964937723500, 135.656423647797, 141.082680593708]
        prices_dates = date_range('2014-12-31', periods=1, freq='D').append(self.return_dates)
        self.test_prices_tms = PricesSeries(data=prices_values, index=prices_dates)
        self.test_dd_prices_tms = PricesSeries(data=[100, 90, 80, 70, 95, 100, 100, 200, 100, 50, 100, 200, 150],
                                               index=date_range('2015-01-01', periods=13, freq='M'))
        self.test_returns = [0.01, 0.02, 0.03, 0.02, 0.01, 0, -0.01, -0.02, 0.01, 0.03, 0.05, 0.04, 0.03, 0.02,
                             0.01, 0, 0.01, 0.03, 0.02, 0.04]
        self.test_simple_returns_tms = SimpleReturnsSeries(data=self.test_returns, index=self.return_dates, dtype=float)

    def test_compound_annual_growth_rate(self):
        expected_return = 535.67015428006502590536838042708
        actual_return = cagr(self.test_simple_returns_tms)
        self.assertAlmostEqual(expected_return, actual_return)

    def test_compound_annual_growth_rate_monthly(self):
        actual_return = cagr(self.test_dd_prices_tms)
        expected_return = pow(1.5, 12.0 / 12.0) - 1
        self.assertAlmostEqual(expected_return, actual_return, delta=0.001)

    def test_annualise_total_return(self):
        simple_return = 2.38989
        expected = simple_return
        actual = annualise_total_return(simple_return, 1, returns_type=SimpleReturnsSeries)
        self.assertEqual(expected, actual)
        actual = annualise_total_return(simple_return, 1, returns_type=LogReturnsSeries)
        self.assertEqual(expected, actual)

        simple_return = 3
        expected = 1
        actual = annualise_total_return(simple_return, 2, returns_type=SimpleReturnsSeries)
        self.assertEqual(expected, actual)

        expected = 0.5
        actual = annualise_total_return(3.5, 7, returns_type=LogReturnsSeries)
        self.assertEqual(expected, actual)

    def test_tail_events(self):
        expected_dates = DatetimeIndex(['2015-01-06', '2015-01-07', '2015-01-08', '2015-01-16'], freq=None)
        expected_benchmark_tail = SimpleReturnsSeries(index=expected_dates, data=[0, -0.01, -0.02, 0])
        expected_examined_tail = SimpleReturnsSeries(index=expected_dates, data=[0.02, 0.01, 0.00, 0.02])

        actual_benchmark_tail, actual_examined_tail = \
            tail_events(self.test_simple_returns_tms, self.test_simple_returns_tms + 0.02, 25.0)

        assert_series_equal(expected_benchmark_tail, actual_benchmark_tail)
        assert_series_equal(expected_examined_tail, actual_examined_tail)

    def test_total_cumulative_return(self):
        # Test simple returns.
        expected_total_return = 0.41082680593708
        actual_total_return = self.test_simple_returns_tms.total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

        log_returns = self.test_simple_returns_tms.to_log_returns()
        actual_total_return = log_returns.total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

        prices = self.test_simple_returns_tms.to_prices()
        actual_total_return = prices.total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

        # Test log returns.
        actual_total_return = log_returns.to_simple_returns().total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

        actual_total_return = log_returns.to_prices().total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

        # Test prices series.
        actual_total_return = prices.to_simple_returns().total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

        actual_total_return = prices.to_log_returns().total_cumulative_return()
        self.assertAlmostEqual(expected_total_return, actual_total_return)

    def test_max_drawdown(self):
        expected_max_drawdown = 0.0298
        actual_max_drawdown = max_drawdown(self.test_prices_tms)
        self.assertAlmostEqual(expected_max_drawdown, actual_max_drawdown, delta=0.00000001)

        expected_max_drawdown = 0.3
        prices_tms = PricesSeries(data=[100, 90, 80, 85, 70, 100], index=date_range('2015-01-01', periods=6))
        actual_max_drawdown = max_drawdown(prices_tms)
        self.assertAlmostEqual(expected_max_drawdown, actual_max_drawdown, places=10)

        expected_max_drawdown = 0.35
        prices_tms = PricesSeries(data=[100, 90, 80, 85, 70, 100, 90, 95, 65],
                                  index=date_range('2015-01-01', periods=9))
        actual_max_drawdown = max_drawdown(prices_tms)
        self.assertEqual(expected_max_drawdown, actual_max_drawdown)

    def test_drawdown_tms(self):
        test_prices = [100, 90, 80, 85, 70, 100, 90, 95, 65]
        prices_tms = PricesSeries(data=test_prices, index=date_range('2015-01-01', periods=9))

        expected_drawdown_values = [0, 0.1, 0.2, 0.15, 0.3, 0, 0.1, 0.05, 0.35]
        expected_drawdowns_tms = QFSeries(expected_drawdown_values, date_range('2015-01-01', periods=9))
        actual_drawdowns_tms = drawdown_tms(prices_tms)

        assert_series_equal(expected_drawdowns_tms, actual_drawdowns_tms)

    def test_cvar(self):
        actual_cvar = cvar(self.test_simple_returns_tms, 0.05)
        expected_cvar = -0.02
        self.assertAlmostEqual(expected_cvar, actual_cvar, places=15)

        expected_cvar = -0.015
        actual_cvar = cvar(self.test_simple_returns_tms, 0.1)
        self.assertAlmostEqual(expected_cvar, actual_cvar, places=15)

    def test_omega_ratio(self):
        actual_omega_ratio = omega_ratio(self.test_simple_returns_tms, threshold=0.0)
        expected_omega_ratio = 38 / 3
        self.assertAlmostEqual(expected_omega_ratio, actual_omega_ratio, delta=0.0000000001)

        actual_omega_ratio = omega_ratio(self.test_simple_returns_tms, threshold=0.1)
        expected_omega_ratio = 0
        self.assertAlmostEqual(expected_omega_ratio, actual_omega_ratio, delta=0.0000000001)

        actual_omega_ratio = omega_ratio(self.test_simple_returns_tms, threshold=0.02)
        expected_omega_ratio = 11 / 16
        self.assertAlmostEqual(expected_omega_ratio, actual_omega_ratio, delta=0.0000000001)

    def test_duration_of_drawdowns(self):
        series_of_max_drawdowns, duration_of_drawdowns = list_of_max_drawdowns(self.test_dd_prices_tms)
        drawdowns = [0.3, 0.75, 0.25]
        durations = [150, 122, 31]
        assert_lists_equal(durations, duration_of_drawdowns)
        assert_lists_equal(drawdowns, series_of_max_drawdowns)

    def test_avg_drawdown_duration(self):
        avg_duration = avg_drawdown_duration(self.test_dd_prices_tms)
        self.assertEqual(avg_duration, (150 + 122 + 31) / 3.0)

    def test_avg_drawdown(self):
        avg_drawdown_value = avg_drawdown(self.test_dd_prices_tms)
        dd_tms = drawdown_tms(self.test_dd_prices_tms)
        self.assertEqual(avg_drawdown_value, dd_tms.mean())

    def test_beta_and_alpha(self):
        dates = date_range(start='2015-01-01', periods=10, freq='d')
        series_values = [i for i in range(1, 21, 2)]
        benchmark_values = [i for i in range(0, 10)]
        series_tms = SimpleReturnsSeries(data=series_values, index=dates).to_prices()
        benchmark_tms = SimpleReturnsSeries(data=benchmark_values, index=dates)
        actual_beta, actual_alpha = beta_and_alpha(series_tms, benchmark_tms)

        epsilon = 0.000000001
        expected_beta = 2.0
        expected_alpha = 1.0

        self.assertAlmostEqual(expected_beta, actual_beta, delta=epsilon)
        self.assertAlmostEqual(expected_alpha, actual_alpha, delta=epsilon)

        series_values[0] += 1
        series_values[1] -= 1
        series_tms = SimpleReturnsSeries(data=series_values, index=dates)
        benchmark_tms = SimpleReturnsSeries(data=benchmark_values, index=dates)
        actual_beta, actual_alpha = beta_and_alpha(series_tms, benchmark_tms)

        expected_beta = 1.9878787878787878
        expected_alpha = 1.0545454545454569

        self.assertAlmostEqual(expected_beta, actual_beta, delta=epsilon)
        self.assertAlmostEqual(expected_alpha, actual_alpha, delta=epsilon)

    def test_get_aggregate_returns_with_simple_returns(self):
        test_returns = [1, 1, 1, 1]
        dates = DatetimeIndex(['2015-12-01', '2016-05-05', '2016-10-01', '2017-01-05'])
        simple_returns_series = SimpleReturnsSeries(data=test_returns, index=dates)

        expected_cumulative_returns = [1.0, 3.0, 1.0]
        expected_result = SimpleReturnsSeries(data=expected_cumulative_returns, index=DatetimeIndex([
            '2015-12-31', '2016-12-31', '2017-12-31']))
        actual_result = get_aggregate_returns(simple_returns_series, convert_to=Frequency.YEARLY)
        assert_series_equal(expected_result, actual_result)

        expected_result = SimpleReturnsSeries(data=[1, 1, 1, 1], index=DatetimeIndex([
            '2015-12-31', '2016-05-31', '2016-10-31', '2017-01-31']))
        actual_result = get_aggregate_returns(simple_returns_series, convert_to=Frequency.MONTHLY)
        assert_series_equal(expected_result, actual_result)

        actual_result = get_aggregate_returns(simple_returns_series, convert_to=Frequency.MONTHLY, multi_index=True)
        actual_result = actual_result.unstack()
        self.assertEqual(actual_result[1].values[2], 1.0)
        self.assertEqual(actual_result[5].values[1], 1.0)
        self.assertEqual(actual_result[10].values[1], 1.0)
        self.assertEqual(actual_result[12].values[0], 1.0)

    def test_get_aggregate_returns_with_log_returns(self):
        test_returns = [0.01] * 22
        dates = DatetimeIndex(
            ['2000-01-15', '2000-01-17', '2000-01-19', '2000-01-21', '2000-01-23', '2000-01-25', '2000-01-27',
             '2000-01-29', '2000-01-31', '2000-02-02', '2000-02-04', '2000-03-05', '2000-04-04', '2000-05-04',
             '2000-06-03', '2000-07-03', '2001-01-19', '2001-08-07', '2002-02-23', '2002-09-11', '2003-03-30',
             '2003-10-16'])
        log_returns_series = LogReturnsSeries(data=test_returns, index=dates)

        expected_result = log_returns_series.to_simple_returns()
        actual_result = get_aggregate_returns(log_returns_series, convert_to=Frequency.DAILY)
        assert_series_equal(expected_result, actual_result)

        expected_cumulative_returns = \
            [0.01, 0.04, 0.03, 0.03, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
        expected_dates = DatetimeIndex([
            '2000-01-14', '2000-01-21', '2000-01-28', '2000-02-04', '2000-03-03', '2000-04-07', '2000-05-05',
            '2000-06-02', '2000-07-07', '2001-01-19', '2001-08-10', '2002-02-22', '2002-09-13', '2003-03-28',
            '2003-10-17'])
        expected_result = LogReturnsSeries(data=expected_cumulative_returns, index=expected_dates).to_simple_returns()
        actual_result = get_aggregate_returns(log_returns_series, convert_to=Frequency.WEEKLY)
        assert_series_equal(expected_result, actual_result)

        expected_cumulative_returns = \
            [0.09, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
        expected_dates = DatetimeIndex([
            '2000-01-31', '2000-02-29', '2000-03-31', '2000-04-30', '2000-05-31', '2000-06-30', '2000-07-31',
            '2001-01-31', '2001-08-31', '2002-02-28', '2002-09-30', '2003-03-31', '2003-10-31'])
        expected_result = LogReturnsSeries(data=expected_cumulative_returns, index=expected_dates).to_simple_returns()
        actual_result = get_aggregate_returns(log_returns_series, convert_to=Frequency.MONTHLY)
        assert_series_equal(expected_result, actual_result)

        expected_cumulative_returns = [0.16, 0.02, 0.02, 0.02]
        expected_dates = DatetimeIndex(['2000-12-31', '2001-12-31', '2002-12-31', '2003-12-31'])
        expected_result = LogReturnsSeries(data=expected_cumulative_returns, index=expected_dates).to_simple_returns()
        actual_result = get_aggregate_returns(log_returns_series, convert_to=Frequency.YEARLY)
        assert_series_equal(expected_result, actual_result)


if __name__ == '__main__':
    unittest.main()
