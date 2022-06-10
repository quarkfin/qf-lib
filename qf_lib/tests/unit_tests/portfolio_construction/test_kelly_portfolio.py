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

from qf_lib.tests.unit_tests.portfolio_construction.utils import assets_df
from qf_lib.portfolio_construction.portfolio_models.kelly_portfolio import KellyPortfolio


class TestKellyPortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df

    def test_get_weights(self):
        cov = self.assets_df.cov()
        mean = self.assets_df.mean(axis=0)
        kp = KellyPortfolio(cov, mean)
        actual_weights = kp.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[18] = 0.8203
        expected_weights_vals[19] = 0.1797

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=1e-04))

    def test_get_weights_with_upper_limits(self):
        cov = self.assets_df.cov()
        mean = self.assets_df.mean(axis=0)
        kp = KellyPortfolio(cov, mean, upper_constraint=0.1)
        actual_weights = kp.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[0] = 0.0628
        expected_weights_vals[4] = 0.1
        expected_weights_vals[6] = 0.1
        expected_weights_vals[7] = 0.1
        expected_weights_vals[8] = 0.0372
        expected_weights_vals[10] = 0.1
        expected_weights_vals[11] = 0.1
        expected_weights_vals[13] = 0.1
        expected_weights_vals[17] = 0.1
        expected_weights_vals[18] = 0.1
        expected_weights_vals[19] = 0.1

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=1e-03))


if __name__ == '__main__':
    unittest.main()
