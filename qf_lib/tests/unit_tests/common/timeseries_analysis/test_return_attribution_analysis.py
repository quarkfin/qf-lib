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

from qf_lib.common.timeseries_analysis.return_attribution_analysis import ReturnAttributionAnalysis
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal


class TestReturnAttributionAnalysis(TestCase):
    def setUp(self):
        dates_span = 100
        regressor_names = ['a', 'b', 'c']

        dates = pd.date_range(start='2015-01-01', periods=dates_span, freq='D')

        fund_returns_tms = SimpleReturnsSeries(data=[i / 100 for i in range(1, dates_span + 1)], index=dates)
        deviation = 0.005
        fit_returns_tms = SimpleReturnsSeries(data=(fund_returns_tms.values + deviation), index=dates)

        regressors_returns_df = SimpleReturnsDataFrame(
            data=np.array([fund_returns_tms, fund_returns_tms + deviation, fund_returns_tms - deviation]).T,
            index=dates, columns=regressor_names
        )
        coefficients = QFSeries(index=regressor_names, data=[1.0, 1.0, 1.0])

        self.fund_returns_tms = fund_returns_tms
        self.fit_returns_tms = fit_returns_tms
        self.regressors_returns_df = regressors_returns_df
        self.coefficients = coefficients

        self.alpha = 0.005

    def test_get_factor_return_attribution(self):
        actual_regressors_return, actual_unexplained_return = ReturnAttributionAnalysis.get_factor_return_attribution(
            self.fund_returns_tms, self.fit_returns_tms, self.regressors_returns_df, self.coefficients, self.alpha
        )
        expected_regressors_return = QFSeries(data=1.0e+61 * np.array([7.8183, 7.8578, 7.7788]),
                                              index=self.coefficients.index)
        expected_unexplained_return = -1.6784e+62
        assert_series_equal(expected_regressors_return, actual_regressors_return, absolute_tolerance=1.0e57)
        self.assertAlmostEqual(expected_unexplained_return / 1e+62, actual_unexplained_return / 1e+62, delta=1e-05)


if __name__ == '__main__':
    unittest.main()
