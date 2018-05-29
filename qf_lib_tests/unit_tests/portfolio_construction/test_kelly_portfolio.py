import unittest
from unittest import TestCase

import numpy as np

from qf_lib_tests.unit_tests.portfolio_construction.utils import assets_df

try:
    import cvxopt
    cvxopt_missing = False
    from qf_lib.portfolio_construction.portfolio_models.kelly_portfolio import KellyPortfolio
except ImportError:
    cvxopt_missing = True


@unittest.skipIf(cvxopt_missing, "Couldn't import cvxopt library")
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
