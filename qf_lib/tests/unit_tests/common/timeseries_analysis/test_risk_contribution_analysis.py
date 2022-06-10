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
import pandas as pd

from qf_lib.common.timeseries_analysis.risk_contribution_analysis import RiskContributionAnalysis
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestRiskContributionAnalysis(TestCase):
    def setUp(self):
        portfolio_rets = [0.01, 0.02, -0.03, 0.04, -0.05, 0.06]
        asset_1_rets = [0.011, 0.035, -0.028, 0.039, -0.044, 0.061]
        asset_2_rets = [0.02, 0.04, -0.06, 0.08, -0.1, 0.12]
        dates = pd.date_range(start='2015-02-01', periods=6)

        self.portfolio_tms = SimpleReturnsSeries(portfolio_rets, dates)
        returns_array = np.array([asset_1_rets, asset_2_rets]).T
        self.factors_df = SimpleReturnsDataFrame(data=returns_array, index=dates, columns=['a', 'b'])

    def test_get_risk_contribution(self):
        weights = QFSeries([0.5, 0.5], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.get_risk_contribution(factors_rets=self.factors_df,
                                                                       weigths_of_assets=weights,
                                                                       portfolio_rets=self.portfolio_tms)
        expected_result = QFSeries([0.32739478440485410, 0.672605215595146], index=self.factors_df.columns)
        assert_series_equal(expected_result, actual_result)

        weights = QFSeries([0.25, 0.75], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.get_risk_contribution(factors_rets=self.factors_df,
                                                                       weigths_of_assets=weights,
                                                                       portfolio_rets=self.portfolio_tms)
        expected_result = QFSeries([0.139601453264340, 0.860398546735660], index=self.factors_df.columns)
        assert_series_equal(expected_result, actual_result)

    def test_get_risk_contribution_optimised(self):
        weights = QFSeries([0.5, 0.5], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.get_risk_contribution_optimised(assets_rets=self.factors_df,
                                                                                 weights_of_assets=weights)
        expected_result = QFSeries([0.328845104104390, 0.671154895895610], index=self.factors_df.columns)
        assert_series_equal(expected_result, actual_result)

        weights = QFSeries([0.25, 0.75], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.get_risk_contribution_optimised(assets_rets=self.factors_df,
                                                                                 weights_of_assets=weights)
        expected_result = QFSeries([0.139939367445589, 0.860060632554411], index=self.factors_df.columns)
        assert_series_equal(expected_result, actual_result)

    def test_get_distance_to_equal_risk_contrib(self):
        factors_covariance = self.factors_df.cov()
        weights = QFSeries([0.5, 0.5], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.get_distance_to_equal_risk_contrib(factors_covariance, weights)
        expected_result = 0.342309791791
        self.assertAlmostEqual(actual_result, expected_result, places=10)

        weights = QFSeries([0.25, 0.75], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.get_distance_to_equal_risk_contrib(factors_covariance, weights)
        expected_result = 0.72012126510882146
        self.assertAlmostEqual(actual_result, expected_result, places=10)

    def test_is_equal_risk_contribution(self):
        asset_a_tms = self.factors_df.loc[:, 'a']
        factors_df = pd.concat((asset_a_tms, asset_a_tms), axis=1)
        factors_df = cast_dataframe(factors_df, SimpleReturnsDataFrame)
        factors_df.columns = ['a', 'b']
        factors_covariance = factors_df.cov()

        weights = QFSeries([0.25, 0.75], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.is_equal_risk_contribution(factors_covariance, weights)
        self.assertFalse(actual_result)

        weights = QFSeries([0.5, 0.5], index=self.factors_df.columns)
        actual_result = RiskContributionAnalysis.is_equal_risk_contribution(factors_covariance, weights)
        self.assertTrue(actual_result)


if __name__ == '__main__':
    unittest.main()
