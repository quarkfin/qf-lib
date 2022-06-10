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

from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal
from qf_lib.tests.unit_tests.common.utils.factorization.factorization_test_utils import get_analysed_tms_and_regressors

from qf_lib.common.utils.factorization.factors_identification.elastic_net_factors_identifier \
    import ElasticNetFactorsIdentifier
from qf_lib.common.utils.factorization.factors_identification.elastic_net_factors_identifier_simplified import \
    ElasticNetFactorsIdentifierSimplified
from qf_lib.common.utils.factorization.factors_identification.stepwise_factor_identifier \
    import StepwiseFactorsIdentifier


class TestFactorsIdentifier(TestCase):

    def setUp(self):
        self.analysed_tms, self.regressors_df = get_analysed_tms_and_regressors()

    def test_stepwise_factors_identification(self):
        stepwise_factors_identifier = StepwiseFactorsIdentifier(is_intercept=False, epsilon=0.01)
        actual_df = stepwise_factors_identifier.select_best_factors(self.regressors_df, self.analysed_tms)
        expected_df = self.regressors_df.loc[:, ['a', 'b']]

        assert_dataframes_equal(expected_df, actual_df)

    def test_enet_factors_identification(self):
        enet_factors_identifier = ElasticNetFactorsIdentifier(max_number_of_regressors=10)
        actual_df = enet_factors_identifier.select_best_factors(self.regressors_df, self.analysed_tms)
        expected_df = self.regressors_df.loc[:, ['a', 'b']]

        assert_dataframes_equal(expected_df, actual_df)

    def test_enet_factors_identification_simplified(self):
        enet_factors_identifier = ElasticNetFactorsIdentifierSimplified(epsilon=0.05)
        actual_df = enet_factors_identifier.select_best_factors(self.regressors_df, self.analysed_tms)
        expected_df = self.regressors_df.loc[:, ['a', 'b']]

        assert_dataframes_equal(expected_df, actual_df)


if __name__ == '__main__':
    unittest.main()
