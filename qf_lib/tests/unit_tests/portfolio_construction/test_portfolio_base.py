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
from os.path import join, dirname
from unittest import TestCase

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.excel.excel_importer import ExcelImporter
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal
from qf_lib.tests.unit_tests.portfolio_construction.utils import assets_df


class TestPortfolio(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets_df = assets_df
        cls.weights_full_invest = QFSeries(
            data=[0.0798, 0.0472, 0.086, 0.0581, 0.0875, 0.0219, 0.0616, 0.0263, 0.0612, 0.0633,
                  0.0062, 0.0232, 0.0204, 0.0609, 0.0769, 0.0314, 0.0711, 0.0615, 0.0006, 0.0549],
            index=assets_df.columns.copy())

        cls.weights_not_full_invest = QFSeries(
            data=[0.059850, 0.035400, 0.064500, 0.043575, 0.065625, 0.016425, 0.046200, 0.019725,
                  0.045900, 0.047475, 0.004650, 0.017400, 0.015300, 0.045675, 0.057675, 0.023550,
                  0.053325, 0.046125, 0.000450, 0.041175],
            index=assets_df.columns.copy())

        cls._load_results_data()

    @classmethod
    def _load_results_data(cls):
        excel_importer = ExcelImporter()  # type: ExcelImporter
        input_data_path = join(dirname(__file__), 'test_portfolio_base_results.xlsx')
        cls.rets_for_fully_invested_const_weights = excel_importer.import_container(
            input_data_path, 'D5', 'D508', SimpleReturnsSeries, sheet_name='returns', include_index=False
        )
        cls.rets_for_not_fully_invested_const_weights = excel_importer.import_container(
            input_data_path, 'J5', 'J508', SimpleReturnsSeries, sheet_name='returns', include_index=False
        )
        cls.rets_for_fully_invested_drift_weights = excel_importer.import_container(
            input_data_path, 'E5', 'E508', SimpleReturnsSeries, sheet_name='returns', include_index=False
        )
        cls.rets_for_not_fully_invested_drift_weights = excel_importer.import_container(
            input_data_path, 'K5', 'K508', SimpleReturnsSeries, sheet_name='returns', include_index=False
        )
        cls.alloc_for_not_fully_invested_drift_weights = excel_importer.import_container(
            input_data_path, 'C4', 'V507', QFDataFrame, sheet_name='drifting weights - alloc 75%',
            include_index=False
        )
        cls.alloc_for_fully_invested_drift_weights = excel_importer.import_container(
            input_data_path, 'C4', 'V507', QFDataFrame, sheet_name='drifting weights - alloc 100%',
            include_index=False
        )

        # set proper index for all of the loaded results
        for returns_tms in [cls.rets_for_fully_invested_const_weights, cls.rets_for_not_fully_invested_const_weights,
                            cls.rets_for_fully_invested_drift_weights, cls.rets_for_not_fully_invested_drift_weights,
                            cls.alloc_for_not_fully_invested_drift_weights, cls.alloc_for_fully_invested_drift_weights]:
            returns_tms.index = assets_df.index.copy()

    def test_constant_weights_fully_invested(self):
        expected_series = self.rets_for_fully_invested_const_weights
        actual_series, _ = Portfolio.constant_weights(self.assets_df, self.weights_full_invest)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=1e-06)

    def test_constant_weights_rets_not_fully_invested(self):
        expected_series = self.rets_for_not_fully_invested_const_weights
        actual_series, _ = Portfolio.constant_weights(self.assets_df, self.weights_not_full_invest)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=1e-06)

    def test_drifting_weights_fully_invested(self):
        expected_series = self.rets_for_fully_invested_drift_weights
        actual_series, _ = Portfolio.drifting_weights(self.assets_df, self.weights_full_invest)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=1e-06)

    def test_drifting_weights_not_fully_invested(self):
        expected_series = self.rets_for_not_fully_invested_drift_weights
        actual_series, _ = Portfolio.drifting_weights(self.assets_df, self.weights_not_full_invest)
        assert_series_equal(expected_series, actual_series, absolute_tolerance=1e-06)

    def test_drifting_weights_alloc_fully_invested(self):
        expected_df = self.alloc_for_fully_invested_drift_weights
        _, actual_df = Portfolio.drifting_weights(self.assets_df, self.weights_full_invest)
        assert_dataframes_equal(expected_df, actual_df, absolute_tolerance=1e-04)

    def test_drifting_weights_alloc_not_fully_invested(self):
        expected_df = self.alloc_for_not_fully_invested_drift_weights
        _, actual_df = Portfolio.drifting_weights(self.assets_df, self.weights_not_full_invest)
        assert_dataframes_equal(expected_df, actual_df, absolute_tolerance=1e-06)


if __name__ == '__main__':
    unittest.main()
