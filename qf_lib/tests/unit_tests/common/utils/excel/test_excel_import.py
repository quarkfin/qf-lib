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

import numpy as np
from os.path import dirname, join
from pandas import DatetimeIndex, concat, date_range

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.documents_utils.excel.excel_importer import ExcelImporter
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal
from qf_lib.tests.helpers.testing_tools.test_case import TestCaseWithFileOutput


from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.unit_tests.common.utils.excel.constants import SINGLE_SHEET_ONE_SERIES, SINGLE_SHEET_ONE_DATA_FRAME, \
    SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME, SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME_SHIFTED


class TestExcelImport(TestCaseWithFileOutput):
    _tmp_dir = join(dirname(__file__), 'tmp')
    _templates_dir = join(dirname(__file__), 'dummies')

    def setUp(self):
        dates = DatetimeIndex(date_range(start='2014-01-01', freq='d', periods=10))
        returns = np.arange(0, 1, 0.1)
        self.test_series = QFSeries(index=dates, data=returns)

        reversed_returns = returns[::-1]
        test_series_reversed = QFSeries(index=dates, data=reversed_returns)

        self.test_data_frame = concat([self.test_series, test_series_reversed], axis=1, join='inner')

        self.xl_importer = ExcelImporter()

    def tearDown(self):
        self.clear_tmp_dir()

    def tmp_dir(self):
        return self._tmp_dir

    def templates_dir(self):
        return self._templates_dir

    def test_import_series(self):
        template_file_path = self.template_file_path(SINGLE_SHEET_ONE_SERIES)

        imported_series = self.xl_importer.import_container(file_path=template_file_path, container_type=QFSeries,
                                                            starting_cell='A1', ending_cell='B10')
        assert_series_equal(self.test_series, imported_series)

    def test_import_dataframe(self):
        template_file_path = self.template_file_path(SINGLE_SHEET_ONE_DATA_FRAME)

        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=QFDataFrame,
                                                               starting_cell='A1', ending_cell='C10')

        assert_dataframes_equal(self.test_data_frame, imported_dataframe)

    def test_import_custom_dataframe(self):
        template_file_path = self.template_file_path(SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME)

        df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=QFDataFrame,
                                                               starting_cell='A10', ending_cell='C15',
                                                               include_index=True, include_column_names=True)

        assert_dataframes_equal(df, imported_dataframe)

    def test_import_custom_dataframe_shifted(self):
        # This tests issue #79.
        template_file_path = self.template_file_path(SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME_SHIFTED)

        # With index and column names.
        df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=QFDataFrame,
                                                               starting_cell='C10', ending_cell='E15',
                                                               include_index=True, include_column_names=True)

        assert_dataframes_equal(df, imported_dataframe)

        # With index and no column names.
        df = QFDataFrame({0: [1, 2, 3, 4, 5], 1: [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=QFDataFrame,
                                                               starting_cell='C11', ending_cell='E15',
                                                               include_index=True, include_column_names=False)

        assert_dataframes_equal(df, imported_dataframe)

        # With column names and no index.
        df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]})
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=QFDataFrame,
                                                               starting_cell='D10', ending_cell='E15',
                                                               include_index=False, include_column_names=True)

        assert_dataframes_equal(df, imported_dataframe)

        # With no column names and no index.
        df = QFDataFrame({0: [1, 2, 3, 4, 5], 1: [10, 20, 30, 40, 50]})
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=QFDataFrame,
                                                               starting_cell='D11', ending_cell='E15',
                                                               include_index=False, include_column_names=False)

        assert_dataframes_equal(df, imported_dataframe)


if __name__ == '__main__':
    unittest.main()
