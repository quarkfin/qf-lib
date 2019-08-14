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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.volatility.drift_independent_volatility import DriftIndependentVolatility
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame


class TestDriftIndependentVolatilityUtils(TestCase):
    def setUp(self):
        tms = date_range('1991-05-14', periods=12, freq='D')

        open = [100.55, 101.20, 103.29, 99.64, 126.93, 127.38, 125.39, 128.04, 124.17, 122.72, 123.83, 126.74]
        high = [105.16, 105.36, 104.13, 106.35, 130.47, 132.54, 128.83, 131.73, 128.29, 127.16, 126.27, 132.98]
        low = [98.07, 99.43, 100.03, 98.89, 115.37, 122.72, 120.48, 126.39, 121.27, 120.74, 122.01, 126.26]
        close = [101.20, 105.15, 101.12, 104.37, 121.72, 124.73, 125.29, 126.67, 122.92, 124.05, 122.20, 128.19]

        data_2d = array([open, high, low, close]).transpose()
        self.ohlc = PricesDataFrame(data=data_2d, index=tms,
                                    columns=[PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close])

    def test_get_volatility(self):
        expected_volatility = 1.1878815962575748
        actual_volatility = DriftIndependentVolatility.get_volatility(self.ohlc, Frequency.DAILY)
        self.assertAlmostEqual(expected_volatility, actual_volatility)
