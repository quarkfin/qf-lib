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

from numpy import sqrt, array
from pandas import date_range, Timedelta, DatetimeIndex

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.get_values_common_dates import get_values_for_common_dates
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.common.utils.miscellaneous.kelly import kelly_binary, kelly
from qf_lib.common.utils.miscellaneous.volume_weighted_average_price import volume_weighted_average_price
from qf_lib.common.utils.ratios.gain_to_pain_ratio import gain_to_pain_ratio
from qf_lib.common.utils.ratios.sharpe_ratio import sharpe_ratio
from qf_lib.common.utils.volatility.volatility_manager import VolatilityManager
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal


class TestMiscellaneousUtils(TestCase):
    def setUp(self):
        self.return_dates = date_range('2015-01-01', periods=20, freq='D')
        self.test_returns = [0.01, 0.02, 0.03, 0.02, 0.01, 0.00, -0.01, -0.02, 0.01, 0.03, 0.05, 0.04, 0.03, 0.02, 0.01,
                             0.00, 0.01, 0.03, 0.02, 0.04]
        self.test_returns_tms = SimpleReturnsSeries(data=self.test_returns, index=self.return_dates, dtype=float)

        monthly_returns = [0.05, 0.03, -0.1, 0.2, -0.01, -0.01]
        monthly_return_dates = date_range('2015-01-01', periods=6, freq='M')
        self.monthly_ret_series = SimpleReturnsSeries(data=monthly_returns, index=monthly_return_dates, dtype=float)

    def test_annualise_with_sqrt(self):
        actual_annualised_values = annualise_with_sqrt(self.test_returns, frequency=Frequency.DAILY)
        expected_annualised_values = [i * sqrt(252) for i in self.test_returns]

        self.assertEqual(expected_annualised_values, actual_annualised_values)

    def test_exponential_average(self):
        actual_smoothed_series = self.test_returns_tms.exponential_average()

        expected_smoothed_values = [0.01, 0.0194, 0.029364, 0.02056184, 0.0106337104, 0.000638022624, -0.00936171864256,
                                    -0.019361703118554, 0.0082382978128868, 0.028694297868773, 0.048721657872126,
                                    0.040523299472328, 0.03063139796834, 0.0206378838781, 0.010638273032686,
                                    0.00063829638196116, 0.0094382977829177, 0.028766297866975, 0.020525977872019,
                                    0.038831558672321]
        expected_smoothed_series = SimpleReturnsSeries(data=expected_smoothed_values, index=self.return_dates.copy())

        assert_series_equal(expected_smoothed_series, actual_smoothed_series)

        actual_smoothed_series = self.test_returns_tms.exponential_average(lambda_coeff=1)
        expected_smoothed_series = self.test_returns_tms

        assert_series_equal(expected_smoothed_series, actual_smoothed_series)

    def test_to_days(self):
        expected = 3
        actual = to_days(Timedelta('3 days'))
        self.assertEqual(expected, actual)

    def test_get_volume_weighted_average_price(self):
        original_datetimes = date_range('2015-01-01', periods=12, freq='10Min')
        prices_tms = PricesSeries(data=[1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4], index=original_datetimes)
        volumes_tms = QFSeries(data=[1, 2, 3, 4, 1, 2, 4, 3, 2, 1, 3, 4], index=original_datetimes)
        interval = Timedelta('40 min')

        expected_datetimes = date_range('2015-01-01 00:40', periods=2, freq=interval)
        expected_avg_weighted_prices = [3, 2.9]
        expected_prices_tms = PricesSeries(data=expected_avg_weighted_prices, index=expected_datetimes)
        actual_prices_tms = volume_weighted_average_price(prices_tms, volumes_tms, interval)
        assert_series_equal(expected_prices_tms, actual_prices_tms, absolute_tolerance=0.0)

    def test_kelly(self):
        expected_kelly_criterion_value = 57.575757575758
        actual_kelly_criterion_value = kelly(self.test_returns_tms)
        self.assertAlmostEqual(expected_kelly_criterion_value, actual_kelly_criterion_value)

    def kelly_binary(self):
        expected_kelly_criterion_value = 2.2987
        p = 0.5801749
        a = 0.0265798
        b = -0.0320652
        actual_kelly_criterion_value = kelly_binary(p, a, b)
        self.assertAlmostEqual(expected_kelly_criterion_value, actual_kelly_criterion_value, places=4)

    def test_min_max_normalized(self):
        actual_normalized_tms = self.test_returns_tms.min_max_normalized()

        expected_normalized_values = array([3, 4, 5, 4, 3, 2, 1, 0, 3, 5, 7, 6, 5, 4, 3, 2, 3, 5, 4, 6]) / 7
        expected_normalized_tms = SimpleReturnsSeries(data=expected_normalized_values,
                                                      index=self.test_returns_tms.index)

        assert_series_equal(expected_normalized_tms, actual_normalized_tms)

    def test_sharpe_ratio(self):
        actual_sharpe_ratio = sharpe_ratio(self.test_returns_tms, frequency=Frequency.DAILY)
        expected_sharpe_ratio = 23.059159631739007
        self.assertAlmostEqual(expected_sharpe_ratio, actual_sharpe_ratio, places=10)

    def test_gain_to_pain_ratio(self):
        gain_to_pain = gain_to_pain_ratio(self.monthly_ret_series)
        expected_gain_to_pain = 1.33333333333
        self.assertAlmostEqual(expected_gain_to_pain, gain_to_pain, places=10)

    def test_get_values_for_common_dates(self):
        data = range(6)
        dates1 = DatetimeIndex(['2014-12-31', '2015-01-02', '2015-01-04', '2015-01-05', '2015-01-09', '2015-01-10'])
        dates2 = DatetimeIndex(['2015-02-01', '2015-01-02', '2015-01-03', '2015-01-04', '2015-01-05', '2015-01-10'])
        series1 = QFSeries(data=data, index=dates1, name='Series 1')
        series2 = QFSeries(data=data, index=dates2, name='Series 2')
        data_2d = array([data, data]).transpose()
        dataframe1 = QFDataFrame(data=data_2d, index=dates2, columns=['DataFrame Col. A', 'DataFrame Col. B'])

        expected_index = DatetimeIndex(['2015-01-02', '2015-01-04', '2015-01-05', '2015-01-10'])
        expected_data1 = [1, 2, 3, 5]
        expected_series1 = QFSeries(data=expected_data1, index=expected_index, name='Series 1')
        expected_data2 = [1, 3, 4, 5]
        expected_series2 = QFSeries(data=expected_data2, index=expected_index, name='Series 2')
        expected_dataframe = QFDataFrame(data=array([expected_data2, expected_data2]).transpose(), index=expected_index,
                                         columns=['DataFrame Col. A', 'DataFrame Col. B'])

        actual_series1, actual_series2, actual_dataframe = get_values_for_common_dates(series1, series2, dataframe1)

        assert_series_equal(expected_series1, actual_series1)
        assert_series_equal(expected_series2, actual_series2)
        assert_dataframes_equal(expected_dataframe, actual_dataframe)

    def test_volatility_manager(self):
        periods = 20
        returns = []
        for i in range(periods):
            ret = 0.01
            if i >= 10:
                ret = 0.02

            returns.append(ret * pow(-1, i))  # 1, -1, 1 ... -2, 2 -2 ... in %

        dates = date_range('2015-01-01', periods=periods, freq='D')
        series = SimpleReturnsSeries(data=returns, index=dates, name='Series 1')

        vol_manager = VolatilityManager(series)
        window_size = 5
        managed_series, weights_series = vol_manager.get_managed_series(vol_level=0.1, window_size=window_size, lag=1)

        ret = 0.005750
        self.assertAlmostEqual(abs(managed_series[window_size]), ret, places=5)
        self.assertAlmostEqual(abs(managed_series[window_size + 1]), ret, places=5)
        self.assertAlmostEqual(abs(managed_series[-2]), ret, places=5)
        self.assertAlmostEqual(abs(managed_series[-1]), ret, places=5)

    def test_volatility_manager_min_max_leverage(self):
        periods = 20
        returns = []
        for i in range(periods):
            ret = 0.005
            if i >= 10:
                ret = 0.1
            returns.append(ret * pow(-1, i))  # 0.5, -0.5, 0.5 ... -10, 10, -10 ... in %

        dates = date_range('2015-01-01', periods=periods, freq='D')
        series = SimpleReturnsSeries(data=returns, index=dates, name='Series 1')

        min_lev = 0.2
        max_lev = 2
        window_size = 5
        vol_manager = VolatilityManager(series)
        managed_series, weights_series = vol_manager.get_managed_series(vol_level=0.2, window_size=window_size, lag=1,
                                                                        min_leverage=min_lev, max_leverage=max_lev)

        self.assertAlmostEqual(abs(managed_series[window_size]), abs(max_lev * series[window_size]), places=5)
        self.assertAlmostEqual(abs(managed_series[-1]), abs(min_lev * series[-1]), places=5)

        self.assertAlmostEqual(abs(weights_series[window_size]), abs(max_lev), places=5)
        self.assertAlmostEqual(abs(weights_series[-1]), abs(min_lev), places=5)
