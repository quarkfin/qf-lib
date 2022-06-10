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
from pandas import DataFrame, Series

from qf_lib.portfolio_construction.black_litterman.black_litterman import BlackLitterman


# THIS TEST REQUIRES TAU CALCULATION AS: 1 / nr_of_observations


class TestBlackLitterman(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hist_cov_data = np.array([[0.00490, 0.00672, 0.01050, 0.01680],
                                      [0.00672, 0.01440, 0.02520, 0.03600],
                                      [0.01050, 0.02520, 0.09000, 0.14400],
                                      [0.01680, 0.03600, 0.14400, 0.36000]])

        cls.weights_data = [0.05, 0.40, 0.45, 0.10]
        cls.names = ['A1', 'A2', 'A3', 'A4']

        cls.hist_cov = DataFrame(cls.hist_cov_data, columns=cls.names, index=cls.names)
        cls.weights = Series(data=cls.weights_data, index=cls.names)
        cls.number_of_data_points = 120

    def test_bl_model_components(self):
        bl = BlackLitterman(self.hist_cov, self.weights, self.number_of_data_points)

        print("=====> LAMBDA")
        lambda_ = bl.calculate_lambda()
        print(lambda_)
        self.assertAlmostEqual(lambda_, 2.2369058, places=6)

        prior_mean, prior_cov = bl.calculate_prior()
        print("=====> Prior Mean")
        print(prior_mean)
        exact_mean = np.zeros(4)
        exact_mean[0] = 0.0208882
        exact_mean[1] = 0.0470556
        exact_mean[2] = 0.1465285
        exact_mean[3] = 0.2595706
        self.assertTrue(np.allclose(prior_mean, exact_mean, rtol=0, atol=1e-6))

        print("=====> Prior COV")
        print(prior_cov)
        exact_cov = np.zeros([4, 4])
        exact_cov[0, :] = np.array([0.004900, 0.006720, 0.010500, 0.016800])
        exact_cov[1, :] = np.array([0.006720, 0.014400, 0.025200, 0.036000])
        exact_cov[2, :] = np.array([0.010500, 0.025200, 0.090000, 0.144000])
        exact_cov[3, :] = np.array([0.016800, 0.036000, 0.144000, 0.360000])
        exact_cov = 1 / 120 * exact_cov   # tau * cov
        self.assertTrue(np.allclose(prior_cov, exact_cov, rtol=0, atol=1e-6))

        print("=====> Tau")
        print(bl.tau)
        self.assertAlmostEqual(bl.tau, 0.0083333, places=6)

    def test_bl_model_views(self):
        bl = BlackLitterman(self.hist_cov, self.weights, self.number_of_data_points)

        bl.add_relative_view(2, 0, 0.1, 0.02481598)
        bl.add_absolute_view(1, 0.03, 0.010954451)

        print("=====> P")
        print(bl.P)
        exact_P = np.zeros([2, 4])
        exact_P[0, :] = np.array([-1.0, 0.0, 1.0, 0.0])
        exact_P[1, :] = np.array([0.0, 1.0, 0.0, 0.0])
        self.assertTrue(np.allclose(bl.P, exact_P, rtol=0, atol=1e-7))

        print("=====> Q")
        print(bl.Q)
        exact_Q = np.zeros([2, 1])
        exact_Q[0, 0] = 0.1
        exact_Q[1, 0] = 0.03
        self.assertTrue(np.allclose(bl.Q, exact_Q, rtol=0, atol=1e-7))

        print("=====> OMEGA")
        print(bl.Omega)
        exact_Omega = np.zeros([2, 2])
        exact_Omega[0, 0] = 0.00061583
        exact_Omega[1, 1] = 0.00012000
        self.assertTrue(np.allclose(bl.Omega, exact_Omega, rtol=0, atol=1e-7))

    def test_bl_model_posterior(self):
        bl = BlackLitterman(self.hist_cov, self.weights, self.number_of_data_points)
        bl.add_relative_view(2, 0, 0.1, 0.02481598)
        bl.add_absolute_view(1, 0.03, 0.010954451)

        posterior_mean, posterior_cov = bl.calculate_posterior()

        print("=====> POSTERIOR Mean")
        print(posterior_mean)
        exact_mean = np.zeros(4)
        exact_mean[0] = 0.016769
        exact_mean[1] = 0.037529
        exact_mean[2] = 0.124758
        exact_mean[3] = 0.226997
        self.assertTrue(np.allclose(posterior_mean, exact_mean, rtol=0, atol=1e-6))

        print("=====> POSTERIOR COV")
        print(posterior_cov)

        exact_cov = np.zeros([4, 4])
        exact_cov[0, :] = np.array([0.004928, 0.006747, 0.010533, 0.016862])
        exact_cov[1, :] = np.array([0.006747, 0.014455, 0.025269, 0.036091])
        exact_cov[2, :] = np.array([0.010533, 0.025269, 0.090320, 0.144533])
        exact_cov[3, :] = np.array([0.016862, 0.036091, 0.144533, 0.361961])
        self.assertTrue(np.allclose(posterior_cov, exact_cov, rtol=0, atol=1e-6))


if __name__ == '__main__':
    unittest.main()
