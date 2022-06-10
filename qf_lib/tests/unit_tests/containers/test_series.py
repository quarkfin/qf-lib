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

import numpy as np
import pandas as pd
from numpy.ma import exp, array

from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestSeries(TestCase):
    def setUp(self):
        return_dates = pd.date_range('2015-01-01', periods=20, freq='D')
        test_returns = [0.01, 0.02, 0.03, 0.02, 0.01, 0, -0.01, -0.02, 0.01, 0.03, 0.05, 0.04, 0.03, 0.02,
                        0.01, 0, 0.01, 0.03, 0.02, 0.04]
        self.test_simple_returns_tms = SimpleReturnsSeries(data=test_returns, index=return_dates, dtype=float,
                                                           name='Test Name')

        prices_values = [100, 101, 103.02, 106.1106, 108.232812, 109.31514012, 109.31514012, 108.2219887188,
                         106.057548944424, 107.118124433868, 110.331668166884, 115.848251575229, 120.482181638238,
                         124.096647087385, 126.578580029132, 127.844365829424, 127.844365829424, 129.1228094877180,
                         132.9964937723500, 135.656423647797, 141.082680593708]
        prices_dates = pd.date_range('2014-12-31', periods=1, freq='D').append(return_dates)
        self.test_prices_tms = PricesSeries(data=prices_values, index=prices_dates, name='Test Name')

        test_log_returns = [0.009950331, 0.019802627, 0.029558802, 0.019802627, 0.009950331, 0, -0.010050336,
                            -0.020202707, 0.009950331, 0.029558802, 0.048790164, 0.039220713, 0.029558802,
                            0.019802627, 0.009950331, 0, 0.009950331, 0.029558802, 0.019802627, 0.039220713]

        self.test_log_returns_tms = LogReturnsSeries(data=test_log_returns, index=return_dates, dtype=float,
                                                     name='Test Name')

    def test_prices_to_simple_returns(self):
        actual_returns_tms = self.test_prices_tms.to_simple_returns()
        expected_returns_tms = self.test_simple_returns_tms
        self.assertEqual(np.dtype("float64"), actual_returns_tms.dtype)
        assert_series_equal(expected_returns_tms, actual_returns_tms)

    def test_prices_to_log_returns(self):
        actual_log_returns_tms = self.test_prices_tms.to_log_returns()
        expected_log_returns_tms = self.test_log_returns_tms
        self.assertEqual(np.dtype("float64"), actual_log_returns_tms.dtype)
        assert_series_equal(expected_log_returns_tms, actual_log_returns_tms)

    def test_simple_returns_to_prices(self):
        expected_tms = self.test_prices_tms
        actual_tms = self.test_simple_returns_tms.to_prices(initial_price=100)
        self.assertEqual(np.dtype("float64"), actual_tms.dtype)
        assert_series_equal(expected_tms, actual_tms, absolute_tolerance=1e-5)

    def test_simple_returns_to_log_returns(self):
        expected_tms = self.test_log_returns_tms
        actual_tms = self.test_simple_returns_tms.to_log_returns()
        self.assertEqual(np.dtype("float64"), actual_tms.dtype)
        assert_series_equal(expected_tms, actual_tms)

    def test_log_returns_to_prices(self):
        prices_values = array([1, exp(1), exp(2), exp(-1), exp(2)])
        prices_dates = pd.date_range('2015-01-01', periods=5)
        expected = PricesSeries(data=prices_values, index=prices_dates)

        returns_tms = LogReturnsSeries(data=[1, 1, -3, 3], index=expected.index[1::])
        actual = returns_tms.to_prices()
        self.assertEqual(np.dtype("float64"), actual.dtype)
        assert_series_equal(expected, actual)

    def test_log_returns_to_simple_returns(self):
        expected_tms = self.test_simple_returns_tms
        actual_tms = self.test_log_returns_tms.to_simple_returns()
        self.assertEqual(np.dtype("float64"), actual_tms.dtype)
        assert_series_equal(expected_tms, actual_tms)

    def test_infer_interval(self):
        expected_interval = pd.Timedelta("1 day")
        expected_frequency = 1
        actual_interval, actual_frequency = self.test_log_returns_tms.infer_interval()
        self.assertEqual(expected_interval, actual_interval)
        self.assertEqual(expected_frequency, actual_frequency)

        expected_interval = pd.Timedelta("1 day")
        expected_frequency = 2 / 3
        dates = pd.date_range('2016-04-01', periods=4, freq='b')
        test_series = QFSeries(data=[0, 0, 0, 0], index=dates)

        actual_interval, actual_frequency = test_series.infer_interval()

        self.assertEqual(expected_interval, actual_interval)
        self.assertEqual(expected_frequency, actual_frequency)

    def test_cast_series(self):
        actual_casted_series = cast_series(self.test_simple_returns_tms, PricesSeries)
        self.assertEqual(np.dtype("float64"), actual_casted_series.dtype)

        self.assertEqual(PricesSeries, type(actual_casted_series))
        self.assertEqual(list(self.test_simple_returns_tms.values), list(actual_casted_series.values))

    def test_rolling_window(self):
        strategy_dates = pd.date_range('2015-01-01', periods=20, freq='D')
        benchmark_dates = pd.date_range('2015-01-10', periods=20, freq='D')
        data = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
                0.01, 0.01, 0.01, 0.01, 0.01]
        strategy = SimpleReturnsSeries(data=data, index=strategy_dates)
        benchmark = SimpleReturnsSeries(data=data, index=benchmark_dates)

        rolling = strategy.rolling_window_with_benchmark(benchmark, 1, lambda x, y: x.mean() + y.mean())
        self.assertEqual(rolling.iloc[0], 0.02)

        self.assertEqual(rolling.index[0], benchmark_dates[1])
        self.assertEqual(rolling.index[9], benchmark_dates[10])
        self.assertEqual(len(rolling), 10)

        # Test with missing values in the middle.
        strategy_dates = pd.date_range('2015-01-02', periods=3, freq='D')
        benchmark_dates = pd.DatetimeIndex(['2015-01-01', '2015-01-02', '2015-01-04'])
        strategy = SimpleReturnsSeries(data=[0.01, 0.50, 0.01], index=strategy_dates)
        benchmark = SimpleReturnsSeries(data=[0.50, 0.01, 0.01], index=benchmark_dates)
        rolling = strategy.rolling_window_with_benchmark(benchmark, 1, lambda x, y: x.mean() + y.mean())
        self.assertEqual(rolling.iloc[0], 0.02)
