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

from qf_lib.portfolio_construction.portfolio_models.max_diversification_portfolio import \
    MaxDiversificationPortfolio
from qf_lib.tests.unit_tests.portfolio_construction.utils import assets_df


class TestMaxDiversificationPortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df

    def test_get_weights(self):
        portfolio = MaxDiversificationPortfolio(self.assets_df.cov(), self.assets_df.std())
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[1] = 0.0393
        expected_weights_vals[2] = 0.0569
        expected_weights_vals[3] = 0.0249
        expected_weights_vals[5] = 0.1076
        expected_weights_vals[6] = 0.0864
        expected_weights_vals[7] = 0.0830
        expected_weights_vals[9] = 0.0528
        expected_weights_vals[10] = 0.1137
        expected_weights_vals[11] = 0.0664
        expected_weights_vals[12] = 0.0730
        expected_weights_vals[14] = 0.0672
        expected_weights_vals[16] = 0.0584
        expected_weights_vals[17] = 0.0575
        expected_weights_vals[18] = 0.0567
        expected_weights_vals[19] = 0.0562

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=1e-04))

    def test_get_weights_with_upper_limits(self):
        portfolio = MaxDiversificationPortfolio(self.assets_df.cov(), self.assets_df.std(), upper_constraint=0.1)
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[1] = 0.0404
        expected_weights_vals[2] = 0.0583
        expected_weights_vals[3] = 0.0264
        expected_weights_vals[5] = 0.0999
        expected_weights_vals[6] = 0.0876
        expected_weights_vals[7] = 0.0845
        expected_weights_vals[9] = 0.0533
        expected_weights_vals[10] = 0.0999
        expected_weights_vals[11] = 0.0682
        expected_weights_vals[12] = 0.0755
        expected_weights_vals[14] = 0.0682
        expected_weights_vals[16] = 0.0581
        expected_weights_vals[17] = 0.0600
        expected_weights_vals[18] = 0.0604
        expected_weights_vals[19] = 0.0592

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=1e-04))


if __name__ == '__main__':
    unittest.main()
