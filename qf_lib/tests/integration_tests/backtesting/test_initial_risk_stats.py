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
from typing import Sequence
from unittest import TestCase

from qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats import InitialRiskStatsFactory
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal


class TestInitialRiskStatsFactory(TestCase):

    def setUp(self):
        self.initial_risk_stats_factory = InitialRiskStatsFactory(max_accepted_dd=0.2, target_return=0.05)

        self.sample_trades_df = QFDataFrame(data=[
            [-0.11, 0.0, -0.105],
            [-0.11, 0.05, 0.19],
            [0.1, 0.0, 0.0],
            [0.0, 0.0, 0.0]
        ])

    def test_make_scenarios(self):
        initial_risks = [0.01, 0.02, 0.03]

        scenarios = [
            self.sample_trades_df * 1.0, self.sample_trades_df * -1.0, self.sample_trades_df * 2.0
        ]  # type: Sequence[QFDataFrame]

        actual_stats = self.initial_risk_stats_factory.make_stats(initial_risks, scenarios)
        expected_stats = QFDataFrame(
            index=[0.01, 0.02, 0.03], columns=[InitialRiskStatsFactory.FAILED, InitialRiskStatsFactory.SUCCEEDED],
            data=[
                [1 / 3, 2 / 3],
                [0.0, 1 / 3],
                [2 / 3, 1 / 3]
            ]
        )

        assert_dataframes_equal(expected_stats, actual_stats)


if __name__ == '__main__':
    unittest.main()
