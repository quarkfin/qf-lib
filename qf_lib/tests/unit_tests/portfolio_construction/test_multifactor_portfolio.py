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

from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.portfolio_construction.portfolio_models.multifactor_portfolio import MultiFactorPortfolio, \
    PortfolioParameters
from qf_lib.tests.unit_tests.portfolio_construction.utils import assets_df


class TestMultiFactorPortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df
        cls.parameters = PortfolioParameters(0.0001, 0.25, 0.25, 0.5, 0)

    def test_get_weights(self):
        portfolio = MultiFactorPortfolio(self.assets_df.cov(),
                                         self.assets_df.var(),
                                         self.assets_df.mean(),
                                         max_drawdown(self.assets_df),
                                         self.assets_df.skew(),
                                         self.parameters)
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[4] = 0.2802
        expected_weights_vals[6] = 0.0393
        expected_weights_vals[16] = 0.0537
        expected_weights_vals[18] = 0.4746
        expected_weights_vals[19] = 0.1521

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=5e-02))

    def test_get_weights_with_upper_limits(self):
        portfolio = MultiFactorPortfolio(self.assets_df.cov(),
                                         self.assets_df.var(),
                                         self.assets_df.mean(),
                                         max_drawdown(self.assets_df),
                                         self.assets_df.skew(),
                                         self.parameters,
                                         upper_constraint=0.1)
        actual_weights = portfolio.get_weights()

        expected_weights_vals = np.zeros(20)
        expected_weights_vals[0] = 0.1000
        expected_weights_vals[4] = 0.1000
        expected_weights_vals[6] = 0.1000
        expected_weights_vals[7] = 0.1000
        expected_weights_vals[8] = 0.0234
        expected_weights_vals[10] = 0.1000
        expected_weights_vals[11] = 0.0920
        expected_weights_vals[13] = 0.0718
        expected_weights_vals[16] = 0.1000
        expected_weights_vals[17] = 0.0128
        expected_weights_vals[18] = 0.1000
        expected_weights_vals[19] = 0.1000

        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=5e-02))


if __name__ == '__main__':
    unittest.main()
