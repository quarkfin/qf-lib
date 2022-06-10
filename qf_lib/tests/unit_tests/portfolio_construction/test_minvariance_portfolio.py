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

from qf_lib.portfolio_construction.portfolio_models.min_variance_portfolio import MinVariancePortfolio
from qf_lib.tests.unit_tests.portfolio_construction.utils import assets_df


class TestMinVariancePortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df

    def test_get_weights(self):
        portfolio = MinVariancePortfolio(self.assets_df.cov())
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[2] = 0.0566
        expected_weights_vals[4] = 0.2578
        expected_weights_vals[5] = 0.0139
        expected_weights_vals[7] = 0.0884
        expected_weights_vals[9] = 0.0442
        expected_weights_vals[10] = 0.1097
        expected_weights_vals[16] = 0.2323
        expected_weights_vals[18] = 0.122
        expected_weights_vals[19] = 0.0751

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=4e-03))

    def test_get_weights_with_upper_limits(self):
        portfolio = MinVariancePortfolio(self.assets_df.cov(), upper_constraint=0.1)
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[0] = 0.0263
        expected_weights_vals[2] = 0.1
        expected_weights_vals[4] = 0.1
        expected_weights_vals[5] = 0.0314
        expected_weights_vals[6] = 0.0388
        expected_weights_vals[7] = 0.1
        expected_weights_vals[9] = 0.0842
        expected_weights_vals[10] = 0.1
        expected_weights_vals[11] = 0.0379
        expected_weights_vals[12] = 0.0153
        expected_weights_vals[13] = 0.0126
        expected_weights_vals[14] = 0.0309
        expected_weights_vals[15] = 0.0226
        expected_weights_vals[16] = 0.1
        expected_weights_vals[18] = 0.1
        expected_weights_vals[19] = 0.1

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=5e-03))


if __name__ == '__main__':
    unittest.main()
