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

from os.path import dirname, join

import numpy as np
from pandas import DatetimeIndex, concat

from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.excel.excel_files_comparator import ExcelFilesComparator
from qf_lib.get_sources_root import get_src_root
from qf_lib.starting_dir import set_starting_dir_abs_path
from qf_lib_tests.helpers.testing_tools.test_case import TestCaseWithFileOutput
from qf_lib_tests.unit_tests.common.utils.excel.constants import SINGLE_SHEET_ONE_SERIES, SINGLE_SHEET_TWO_SERIES, \
    TWO_SHEETS_TWO_SERIES, TWO_SHEETS_THREE_SERIES, SINGLE_SHEET_ONE_DATA_FRAME, SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME, \
    SINGLE_CELLS
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

set_starting_dir_abs_path(get_src_root())


class TestExcelExport(TestCaseWithFileOutput):
    _tmp_dir = join(dirname(__file__), 'tmp')
    _templates_dir = join(dirname(__file__), 'dummies')

    comparator = ExcelFilesComparator()

    def setUp(self):
        dates = DatetimeIndex(start='2014-01-01', freq='d', periods=10)
        returns = np.arange(0, 1, 0.1)
        self.test_series = QFSeries(index=dates, data=returns)

        reversed_returns = returns[::-1]
        self.test_series_reversed = QFSeries(index=dates, data=reversed_returns)

        self.test_data_frame = concat([self.test_series, self.test_series_reversed], axis=1, join='inner')

        settings = get_test_settings()
        self.xl_exporter = ExcelExporter(settings=settings)

    def tearDown(self):
        self.clear_tmp_dir()

    def tmp_dir(self):
        return self._tmp_dir

    def templates_dir(self):
        return self._templates_dir

    def test_exporting_series_to_the_new_file(self):
        new_file_path = self.tmp_file_path(SINGLE_SHEET_ONE_SERIES)
        expected_file_path = self.template_file_path(SINGLE_SHEET_ONE_SERIES)

        self.xl_exporter.export_container(self.test_series, new_file_path)
        self.comparator.assert_the_same(expected_file_path, new_file_path)

    def test_exporting_series_to_the_existing_file(self):
        """
        Take a workbook with one worksheet and later add a new series to this worksheet without removing the other data
        within the worksheet.
        """
        file_to_modify_path = self.copy_template_to_tmp(SINGLE_SHEET_ONE_SERIES)
        expected_file_path = self.template_file_path(SINGLE_SHEET_TWO_SERIES)

        self.xl_exporter.export_container(self.test_series_reversed, file_to_modify_path, starting_cell='C1')
        self.comparator.assert_the_same(expected_file_path, file_to_modify_path)

    def test_exporting_series_to_the_new_worksheet(self):
        """
        Take the existing workbook, add a new worksheet and save there some data.
        """
        file_to_modify_path = self.copy_template_to_tmp(SINGLE_SHEET_ONE_SERIES)
        expected_file_path = self.template_file_path(TWO_SHEETS_TWO_SERIES)

        self.xl_exporter.export_container(self.test_series_reversed, file_to_modify_path, sheet_name='Sheet2')
        self.comparator.assert_the_same(expected_file_path, file_to_modify_path)

    def test_exporting_series_to_the_existing_worksheet(self):
        file_to_modify_path = self.copy_template_to_tmp(TWO_SHEETS_TWO_SERIES)
        expected_file_path = self.template_file_path(TWO_SHEETS_THREE_SERIES)

        self.xl_exporter.export_container(self.test_series, file_to_modify_path,
                                          sheet_name='Sheet2', starting_cell='C1')
        self.comparator.assert_the_same(expected_file_path, file_to_modify_path)

    def test_exporting_dataframe(self):
        new_file_path = self.tmp_file_path(SINGLE_SHEET_ONE_DATA_FRAME)
        expected_file_path = self.template_file_path(SINGLE_SHEET_ONE_DATA_FRAME)

        self.xl_exporter.export_container(self.test_data_frame, new_file_path)
        self.comparator.assert_the_same(expected_file_path, new_file_path)

    def test_exporting_dataframe_custom_index(self):
        new_file_path = self.tmp_file_path(SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME)
        expected_file_path = self.template_file_path(SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME)

        df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
        self.xl_exporter.export_container(df, new_file_path, starting_cell='A10', include_column_names=True)
        self.comparator.assert_the_same(expected_file_path, new_file_path)

    def test_exporting_single_cells(self):
        new_file_path = self.tmp_file_path(SINGLE_CELLS)
        expected_file_path = self.template_file_path(SINGLE_CELLS)

        self.xl_exporter.write_cell(new_file_path, "A1", "Testing")
        self.xl_exporter.write_cell(new_file_path, "D6", 123456)
        self.xl_exporter.write_cell(new_file_path, "G12", 3.1423456)
        self.comparator.assert_the_same(expected_file_path, new_file_path)
