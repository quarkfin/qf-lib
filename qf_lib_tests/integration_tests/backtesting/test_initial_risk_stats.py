import unittest
from typing import Sequence
from unittest import TestCase

import pandas as pd
from pandas.util.testing import assert_frame_equal

from qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats import InitialRiskStatsFactory


class TestInitialRiskStatsFactory(TestCase):

    def setUp(self):
        self.initial_risk_stats_factory = InitialRiskStatsFactory(max_accepted_dd=0.2, target_return=0.05)

        self.sample_trades_df = pd.DataFrame(data=[
            [-0.11, 0.0, -0.105],
            [-0.11, 0.05, 0.19],
            [0.1, 0.0, 0.0],
            [0.0, 0.0, 0.0]
        ])

    def test_make_scenarios(self):
        initial_risks = [0.01, 0.02, 0.03]

        scenarios = [
            self.sample_trades_df * 1.0, self.sample_trades_df * -1.0, self.sample_trades_df * 2.0
        ]  # type: Sequence[pd.DataFrame]

        actual_stats = self.initial_risk_stats_factory.make_stats(initial_risks, scenarios)
        expected_stats = pd.DataFrame(
            index=[0.01, 0.02, 0.03], columns=[InitialRiskStatsFactory.FAILED, InitialRiskStatsFactory.SUCCEEDED],
            data=[
                [1/3, 2/3],
                [0.0, 1/3],
                [2/3, 1/3]
            ]
        )

        assert_frame_equal(expected_stats, actual_stats)


if __name__ == '__main__':
    unittest.main()
