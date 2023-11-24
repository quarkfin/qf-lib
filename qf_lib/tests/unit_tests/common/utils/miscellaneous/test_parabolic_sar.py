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
import numpy as np

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.miscellaneous.parabolic_sar import parabolic_sar
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class TestParabolicSAR(TestCase):
    def test_psar(self):
        dummy_price_data = {
            PriceField.Low: [1.1, 1.4, 2.6, 3.4, 4.3, 5.1, 4.4, 3.1],
            PriceField.High: [2.6, 2.2, 4.4, 6.5, 7.1, 7.4, 7.6, 5.],
            PriceField.Close: [1.4, 1.2, 3.5, 5.3, 7.1, 6.3, 6.5, 4.2],
        }
        dummy_prices_dataframe = PricesDataFrame(dummy_price_data)

        test_psar_values = [2.600000, 1.400000, 1.502000,
                            1.725920, 2.0663647999999997,
                            2.5090556159999995, 2.7581500543999997]
        calculated_psar = parabolic_sar(dummy_prices_dataframe)

        np.testing.assert_allclose(test_psar_values, calculated_psar.values, rtol=1e-9)
        self.assertListEqual(list(dummy_prices_dataframe.index[1:]),
                             list(calculated_psar.index))
        self.assertIsInstance(calculated_psar, QFSeries)

    def test_psar_with_nan(self):
        dummy_price_data_with_nan = {
            PriceField.Low: [1.1, 1.4, 2.6, 3.4, None, 5.1, 4.4, 3.1],
            PriceField.High: [None, 2.2, None, 6.5, 7.1, 7.4, 7.6, 5.],
            PriceField.Close: [None, 1.2, 3.5, 5.3, 7.1, 6.3, 6.5, 4.2],
        }
        dummy_prices_dataframe_with_nan = PricesDataFrame(dummy_price_data_with_nan)

        test_psar_values_with_nan = [1.2864, 1.530944, 1.89508736, 2.1434803712]
        calculated_psar_with_nan = parabolic_sar(dummy_prices_dataframe_with_nan)

        np.testing.assert_allclose(test_psar_values_with_nan, calculated_psar_with_nan.values, rtol=1e-9)
        self.assertListEqual(list(dummy_prices_dataframe_with_nan.dropna().index[1:]),
                             list(calculated_psar_with_nan.index))
        self.assertIsInstance(calculated_psar_with_nan, QFSeries)


if __name__ == "__main__":
    unittest.main()
