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

from qf_lib.portfolio_construction.portfolio_models.max_excess_return_portfolio import MaxExcessReturnPortfolio
from qf_lib.tests.unit_tests.portfolio_construction.utils import assets_df


class TestMaxExcessReturnPortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df

    def test_get_weights(self):
        portfolio = MaxExcessReturnPortfolio(self.assets_df.cov(), self.assets_df.var())
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[1] = 0.3729
        expected_weights_vals[5] = 0.232
        expected_weights_vals[12] = 0.1086
        expected_weights_vals[17] = 0.2865

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=4e-03))

    def test_get_weights_with_upper_limits(self):
        portfolio = MaxExcessReturnPortfolio(self.assets_df.cov(), self.assets_df.var(), upper_constraint=0.1)
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[1] = 0.1
        expected_weights_vals[2] = 0.029
        expected_weights_vals[3] = 0.1
        expected_weights_vals[5] = 0.1
        expected_weights_vals[6] = 0.1
        expected_weights_vals[7] = 0.0483
        expected_weights_vals[8] = 0.0126
        expected_weights_vals[9] = 0.0366
        expected_weights_vals[10] = 0.0735
        expected_weights_vals[11] = 0.1
        expected_weights_vals[12] = 0.1
        expected_weights_vals[14] = 0.1
        expected_weights_vals[17] = 0.1

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=4e-03))


if __name__ == '__main__':
    unittest.main()
