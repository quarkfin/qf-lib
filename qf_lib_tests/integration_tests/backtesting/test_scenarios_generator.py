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

from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator
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


if __name__ == '__main__':
    unittest.main()
