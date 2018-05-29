from unittest import TestCase

import numpy as np

from qf_lib.portfolio_construction.portfolio_models.risk_parity_portfolio import RiskParityPortfolio
from qf_lib_tests.unit_tests.portfolio_construction.utils import assets_df


class TestRiskParityPortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df

    def test_get_weights(self):
        rpp = RiskParityPortfolio(self.assets_df)
        actual_weights = rpp.get_weights()

        expected_weights_vals = np.array([0.0634, 0.0215, 0.0519, 0.0460, 0.0767,
                                          0.0295, 0.0458, 0.0532, 0.0487, 0.0527,
                                          0.0540, 0.0462, 0.0386, 0.0571, 0.0440,
                                          0.0527, 0.0717, 0.0270, 0.0650, 0.0543])
        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=1e-04))

    def test_get_weights_with_upper_limits(self):
        rpp = RiskParityPortfolio(self.assets_df, upper_constraint=0.06)
        actual_weights = rpp.get_weights()

        expected_weights_vals = np.array([0.0600, 0.0226, 0.0546, 0.0484, 0.0600,
                                          0.0309, 0.0481, 0.0559, 0.0512, 0.0554,
                                          0.0567, 0.0486, 0.0405, 0.0600, 0.0462,
                                          0.0554, 0.0600, 0.0284, 0.0600, 0.0571])
        self.assertTrue(np.allclose(expected_weights_vals, actual_weights.values, rtol=0, atol=1e-04))


if __name__ == '__main__':
    # unittest.main()
    rpp = RiskParityPortfolio(assets_df, upper_constraint=0.06)
    actual_weights = rpp.get_weights()

