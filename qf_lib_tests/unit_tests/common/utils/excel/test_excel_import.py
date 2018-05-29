import unittest

import numpy as np
from os.path import dirname, join
from pandas import DataFrame, DatetimeIndex, concat
from qf_lib_tests.unit_tests.common.utils.excel.constants import SINGLE_SHEET_ONE_SERIES, SINGLE_SHEET_ONE_DATA_FRAME, \
    SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME, SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME_SHIFTED

from qf_lib.common.utils.excel.excel_importer import ExcelImporter
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.testing_tools.containers_comparison import assert_dataframes_equal, assert_series_equal
from qf_lib.testing_tools.test_case import TestCaseWithFileOutput


class TestExcelImport(TestCaseWithFileOutput):
    _tmp_dir = join(dirname(__file__), 'tmp')
    _templates_dir = join(dirname(__file__), 'dummies')

    def setUp(self):
        dates = DatetimeIndex(start='2014-01-01', freq='d', periods=10)
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

        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=DataFrame,
                                                               starting_cell='A1', ending_cell='C10')

        assert_dataframes_equal(self.test_data_frame, imported_dataframe)

    def test_import_custom_dataframe(self):
        template_file_path = self.template_file_path(SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME)

        df = DataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=DataFrame,
                                                               starting_cell='A10', ending_cell='C15',
                                                               include_index=True, include_column_names=True)

        assert_dataframes_equal(df, imported_dataframe)

    def test_import_custom_dataframe_shifted(self):
        # This tests issue #79.
        template_file_path = self.template_file_path(SINGLE_SHEET_CUSTOM_INDEX_DATA_FRAME_SHIFTED)

        # With index and column names.
        df = DataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=DataFrame,
                                                               starting_cell='C10', ending_cell='E15',
                                                               include_index=True, include_column_names=True)

        assert_dataframes_equal(df, imported_dataframe)

        # With index and no column names.
        df = DataFrame({0: [1, 2, 3, 4, 5], 1: [10, 20, 30, 40, 50]},
                       ["A", "B", "C", "D", "E"])
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=DataFrame,
                                                               starting_cell='C11', ending_cell='E15',
                                                               include_index=True, include_column_names=False)

        assert_dataframes_equal(df, imported_dataframe)

        # With column names and no index.
        df = DataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]})
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=DataFrame,
                                                               starting_cell='D10', ending_cell='E15',
                                                               include_index=False, include_column_names=True)

        assert_dataframes_equal(df, imported_dataframe)

        # With no column names and no index.
        df = DataFrame({0: [1, 2, 3, 4, 5], 1: [10, 20, 30, 40, 50]})
        imported_dataframe = self.xl_importer.import_container(file_path=template_file_path, container_type=DataFrame,
                                                               starting_cell='D11', ending_cell='E15',
                                                               include_index=False, include_column_names=False)

        assert_dataframes_equal(df, imported_dataframe)


if __name__ == '__main__':
    unittest.main()
