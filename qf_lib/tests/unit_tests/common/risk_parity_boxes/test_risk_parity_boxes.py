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

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.risk_parity_boxes.risk_parity_boxes import RiskParityBoxesFactory, ChangeDirection
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestRiskParityBoxesFactory(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start_date = str_to_date("2017-10-01")
        cls.end_date = str_to_date("2017-11-01")
        cls.frequency = Frequency.DAILY

        datetime_index = pd.DatetimeIndex([
            '2017-10-02', '2017-10-03', '2017-10-04', '2017-10-05', '2017-10-06',
            '2017-10-09', '2017-10-10', '2017-10-11', '2017-10-12', '2017-10-13',
            '2017-10-16', '2017-10-17', '2017-10-18', '2017-10-19', '2017-10-20',
            '2017-10-23', '2017-10-24', '2017-10-25', '2017-10-26', '2017-10-27',
            '2017-10-30', '2017-10-31', '2017-11-01'
        ])

        bbg_data_provider = Mock(spec=BloombergDataProvider)

        all_tickers_str = ['BCIT3T Index', 'IEF US Equity', 'LQD US Equity', 'MSBIERTR Index', 'MXUS Index',
                           'SPGSCITR Index', 'XAU Curncy']
        all_tickers = BloombergTicker.from_string(all_tickers_str)
        assets_prices_df = PricesDataFrame(index=datetime_index, columns=all_tickers, data=[
            [263.7628, 106.24, 121.02, 321.8249, 2409.48, 2295.60, 1271.13],
            [263.9803, 106.39, 121.29, 322.0949, 2414.41, 2294.91, 1271.66],
            [264.1640, 106.36, 121.22, 322.3203, 2417.31, 2294.28, 1274.85],
            [264.0932, 106.25, 121.05, 322.4172, 2430.80, 2323.34, 1268.22],
            [263.9816, 106.12, 120.95, 322.1411, 2428.16, 2282.24, 1276.68],
            [263.9816, 106.24, 121.05, None, 2423.41, 2284.78, 1284.05],
            [264.4529, 106.28, 121.13, 322.3113, 2428.73, 2318.99, 1288.03],
            [264.5108, 106.40, 121.07, 322.3553, 2433.09, 2324.63, 1291.72],
            [264.8223, 106.50, 121.10, 322.7489, 2428.89, 2314.78, 1293.72],
            [264.9401, 106.86, 121.58, 322.8720, 2430.63, 2342.19, 1303.82],
            [264.2089, 106.68, 121.41, 322.8467, 2434.66, 2353.20, 1295.79],
            [264.0592, 106.64, 121.39, 323.1079, 2436.35, 2345.04, 1285.12],
            [263.9370, 106.37, 121.21, 323.2238, 2438.08, 2345.57, 1281.08],
            [264.0463, 106.48, 121.39, 323.5498, 2439.31, 2332.31, 1290.13],
            [263.8424, 106.04, 121.06, 322.9874, 2451.70, 2340.26, 1280.47],
            [263.8961, 106.14, 121.18, 322.7436, 2441.71, 2343.72, 1282.27],
            [263.7129, 105.82, 120.88, 322.3214, 2445.61, 2366.00, 1276.58],
            [263.3216, 105.65, 120.56, 322.4332, 2434.13, 2364.23, 1277.53],
            [263.3638, 105.51, 120.55, 322.1635, 2438.07, 2376.52, 1266.99],
            [263.8662, 105.85, 120.91, 322.3655, 2457.45, 2396.93, 1273.35],
            [264.4531, 106.23, 121.31, 322.9710, 2449.20, 2407.43, 1276.29],
            [264.4690, 106.16, 121.14, 323.0688, 2452.15, 2415.28, 1271.45],
            [264.4727, 106.06, 121.01, 323.1553, 2455.70, 2415.48, 1274.66]
        ])
        bbg_data_provider.get_price.return_value = assets_prices_df

        cls.bbg_data_provider = bbg_data_provider

    def setUp(self):
        self.risk_parity_boxes_factory = RiskParityBoxesFactory(self.bbg_data_provider)

    def test_make_parity_boxes(self):
        abs_tolerance = 0.0005

        actual_boxes = self.risk_parity_boxes_factory.make_parity_boxes(self.start_date, self.end_date)
        datetime_index = pd.DatetimeIndex([
            '2017-10-03', '2017-10-04', '2017-10-05', '2017-10-06',
            '2017-10-09', '2017-10-10', '2017-10-11', '2017-10-12', '2017-10-13',
            '2017-10-16', '2017-10-17', '2017-10-18', '2017-10-19', '2017-10-20',
            '2017-10-23', '2017-10-24', '2017-10-25', '2017-10-26', '2017-10-27',
            '2017-10-30', '2017-10-31', '2017-11-01'
        ])

        expected_series = SimpleReturnsSeries(index=datetime_index, data=[
            0.000668214, 0.000835684, 0.000837076, -0.001577371, 0.000934, 0.002332372, 0.000723187, 0.000714223,
            0.002511958, -0.00039049, -0.000812991, -0.000116197, 0.0011223, -0.001970612, -0.000243163, -0.000622247,
            0.000292873, -0.001195635, 0.002011089, 0.002190187, 7.02049E-05, 0.000546751
        ])
        actual_series = actual_boxes.get_series(growth=ChangeDirection.RISING, inflation=ChangeDirection.RISING)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=abs_tolerance)

        expected_series = SimpleReturnsSeries(index=datetime_index, data=[
            0.00214062368, 0.00011823259, 0.00133745897, -0.00093319962, .0,
            0.00126311759, 0.00040289465, -0.00051413454, 0.00268699427, -0.00018594003, 0.00017342217, -0.00062892417,
            0.00109962909, 0.00034010165, -0.00100080029, -0.0008813078, -0.00345021469, 0.00057545608, 0.0049085509,
            0.00068356544, -0.00038338606, -0.00010546472
        ])
        actual_series = actual_boxes.get_series(growth=ChangeDirection.RISING, inflation=ChangeDirection.FALLING)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=abs_tolerance)

        expected_series = SimpleReturnsSeries(index=datetime_index, data=[
            0.00075094743, 0.00102506202, -0.00116334637, 0.00086457088, 0.001030, 0.00202367433, 0.00069925268,
            0.00124515552, 0.00178121325, -0.00337692323, -0.00195857117, -0.00094960523, 0.00162098426, -0.00199096335,
            0.00042216467, -0.00137335971, -0.0010796149, -0.00136642671, 0.00247283233, 0.00223942762, -0.00063914336,
            0.00046975
        ])
        actual_series = actual_boxes.get_series(growth=ChangeDirection.FALLING, inflation=ChangeDirection.RISING)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=abs_tolerance)

        expected_series = SimpleReturnsSeries(index=datetime_index, data=[
            0.00112748921, 0.0005160599, -0.00222551401, 0.00103350015, 0.002442, 0.00115561595,
            0.00162539269, 0.00111385182, 0.00464585854, -0.00296358368, -0.00262220629, -0.00270699558, 0.00275822114,
            -0.00509161628, 0.00107539045, -0.00342160737, -0.00093475391, -0.00330513788, 0.003736121, 0.00322371024,
            -0.00155485155, 0.00004935567
        ])
        actual_series = actual_boxes.get_series(growth=ChangeDirection.FALLING, inflation=ChangeDirection.FALLING)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=abs_tolerance)


if __name__ == '__main__':
    unittest.main()
