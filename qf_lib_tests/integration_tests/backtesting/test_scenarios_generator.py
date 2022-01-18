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
from datetime import datetime
from unittest import TestCase

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator
from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.series.qf_series import QFSeries


class TestScenariosGenerator(TestCase):

    def setUp(self):
        self.generator = ScenariosGenerator()

        self.num_of_scenarios = 100000
        self.scenarios_length = 7

    def test_make_scenarios(self):
        first_ret_value = 0.05
        second_ret_value = 0.1

        trade_rets = QFSeries([first_ret_value, second_ret_value])

        scenarios_df = self.generator.make_scenarios(trade_rets, self.scenarios_length, self.num_of_scenarios)

        expected_shape = (self.scenarios_length, self.num_of_scenarios)
        actual_shape = scenarios_df.shape
        self.assertAlmostEqual(expected_shape, actual_shape)

        values_count = scenarios_df.iloc[0, :].value_counts(normalize=True)

        first_return_freq = values_count[first_ret_value]
        second_return_freq = values_count[second_ret_value]

        expected_frequency = 0.5
        self.assertAlmostEqual(first_return_freq, expected_frequency, delta=0.01)
        self.assertAlmostEqual(second_return_freq, expected_frequency, delta=0.01)

    def test_make_exposure_scenarios__daily(self):
        time_in_the_market = 0.30
        num_of_trades = 8
        scenario = self.generator.make_exposure_scenarios(datetime(2021, 10, 1), datetime(2021, 10, 31), num_of_trades,
                                                          time_in_the_market, Exposure.LONG, Frequency.DAILY, seed=10)
        self.assertEqual(scenario.size, 31)
        lengths_of_trades = self._compute_trades_lengths(scenario)

        self.assertAlmostEqual(sum(lengths_of_trades) / 31, time_in_the_market, delta=0.01)
        self.assertEqual(8, len(lengths_of_trades))

    def test_make_exposure_scenarios__daily_2(self):
        """ Test which generates scenarios in case if the number of trades is so big, so that some of the trades will
        not have any gap between themselves. """
        time_in_the_market = 0.80
        num_of_trades = 8
        scenario = self.generator.make_exposure_scenarios(datetime(2021, 10, 1), datetime(2021, 10, 31), num_of_trades,
                                                          time_in_the_market, Exposure.LONG, Frequency.DAILY, seed=10)
        self.assertEqual(scenario.size, 31)
        lengths_of_trades = self._compute_trades_lengths(scenario)

        self.assertAlmostEqual(sum(lengths_of_trades) / 31, time_in_the_market, delta=0.01)
        self.assertEqual(4, len(lengths_of_trades))

    def test_make_exposure_scenarios_with_trades_reduction__daily(self):
        """ Number of trades created will be smaller than the desired number of trades."""
        time_in_the_market = 0.1
        num_of_trades = 8
        scenario = self.generator.make_exposure_scenarios(datetime(2021, 10, 1), datetime(2021, 10, 31), num_of_trades,
                                                          time_in_the_market, Exposure.LONG, Frequency.DAILY, seed=10)
        self.assertEqual(scenario.size, 31)
        lengths_of_trades = self._compute_trades_lengths(scenario)

        self.assertAlmostEqual(sum(lengths_of_trades) / 31, time_in_the_market, delta=0.01)
        self.assertEqual(3, len(lengths_of_trades))

    def test_make_exposure_scenarios__no_time_in_the_market(self):
        time_in_the_market = 0
        num_of_trades = 1
        scenario = self.generator.make_exposure_scenarios(datetime(2021, 10, 1), datetime(2021, 10, 31), num_of_trades,
                                                          time_in_the_market, Exposure.LONG, Frequency.DAILY, seed=10)
        self.assertEqual(scenario.size, 31)
        lengths_of_trades = self._compute_trades_lengths(scenario)

        self.assertAlmostEqual(sum(lengths_of_trades) / 31, time_in_the_market, places=1)
        self.assertEqual(0, len(lengths_of_trades))

    def test_make_exposure_scenarios__no_time_out_of_the_market(self):
        time_in_the_market = 1.0
        num_of_trades = 5
        scenario = self.generator.make_exposure_scenarios(datetime(2021, 10, 1), datetime(2021, 10, 31), num_of_trades,
                                                          time_in_the_market, Exposure.LONG, Frequency.DAILY, seed=10)
        self.assertEqual(scenario.size, 31)
        lengths_of_trades = self._compute_trades_lengths(scenario)

        self.assertAlmostEqual(sum(lengths_of_trades) / 31, time_in_the_market, places=1)
        self.assertEqual(1, len(lengths_of_trades))

    def test_make_exposure_scenarios__intraday(self):
        time_in_the_market = 0.40
        num_of_trades = 2
        scenario = self.generator.make_exposure_scenarios(datetime(2021, 10, 1), datetime(2021, 10, 2), num_of_trades,
                                                          time_in_the_market, Exposure.LONG, Frequency.MIN_60, seed=17)
        self.assertEqual(scenario.size, 25)
        lengths_of_trades = self._compute_trades_lengths(scenario)

        self.assertAlmostEqual(sum(lengths_of_trades) / 25, time_in_the_market)
        self.assertEqual(num_of_trades, len(lengths_of_trades))

    @staticmethod
    def _compute_trades_lengths(exposure_series: QFSeries):
        lengths_of_trades = []
        current_exposure = Exposure.OUT

        trade_length = 0
        for element in exposure_series:
            if element == Exposure.LONG:
                trade_length = trade_length + 1
            elif element == Exposure.OUT and current_exposure == Exposure.LONG:
                lengths_of_trades.append(trade_length)
                trade_length = 0
            current_exposure = element

        if trade_length:
            lengths_of_trades.append(trade_length)
        return lengths_of_trades


if __name__ == '__main__':
    unittest.main()
