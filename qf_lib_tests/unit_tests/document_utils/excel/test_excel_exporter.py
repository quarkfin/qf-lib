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
from unittest.mock import Mock, patch, MagicMock, call

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.documents_utils.excel.write_mode import WriteMode


class TestExcelExporter(unittest.TestCase):

    def setUp(self) -> None:
        load_workbook_patcher = patch('qf_lib.documents_utils.excel.excel_exporter.load_workbook')
        self.load_workbook = load_workbook_patcher.start()
        self.addCleanup(load_workbook_patcher.stop)

        isfile_patcher = patch('qf_lib.documents_utils.excel.excel_exporter.isfile')
        self.isfile = isfile_patcher.start()
        self.addCleanup(isfile_patcher.stop)

        exists_patcher = patch('qf_lib.documents_utils.excel.excel_exporter.exists')
        self.exists = exists_patcher.start()
        self.addCleanup(exists_patcher.stop)

    def test_get_workbook__file_exists__create_if_doesnt_exist(self):
        excel_exporter = ExcelExporter(Mock())
        file_path = Mock()

        # Test when file path exists
        self.exists.return_value = True
        self.isfile.return_value = True

        # Test CREATE_IF_DOESNT_EXIST write mode in case if file exists
        write_mode = WriteMode.CREATE_IF_DOESNT_EXIST
        excel_exporter.get_workbook(file_path, write_mode)
        self.load_workbook.assert_called_once_with(file_path)

    def test_get_workbook__file_exists__create(self):
        excel_exporter = ExcelExporter(Mock())
        file_path = Mock()

        # Test when file path exists
        self.exists.return_value = True
        self.isfile.return_value = True

        # Test CREATE write mode in case if file exists
        with self.assertRaises(AssertionError):
            write_mode = WriteMode.CREATE
            excel_exporter.get_workbook(file_path, write_mode)

    def test_get_workbook__file_exists__open_existing(self):
        excel_exporter = ExcelExporter(Mock())
        file_path = Mock()

        # Test when file path exists
        self.exists.return_value = True
        self.isfile.return_value = True

        # Test OPEN_EXISTING write mode in case if file exists
        write_mode = WriteMode.OPEN_EXISTING
        excel_exporter.get_workbook(file_path, write_mode)
        self.load_workbook.assert_called_once_with(file_path)

    def test_get_workbook__file_does_not_exist__open_existing(self):
        excel_exporter = ExcelExporter(Mock())
        file_path = Mock()

        # Test OPEN_EXISTING write mode in case if path exists, but points to a directory
        self.exists.return_value = True
        self.isfile.return_value = False

        with self.assertRaises(AssertionError):
            write_mode = WriteMode.OPEN_EXISTING
            excel_exporter.get_workbook(file_path, write_mode)
            self.load_workbook.assert_not_called()

    @patch('qf_lib.documents_utils.excel.excel_exporter.makedirs')
    @patch('qf_lib.documents_utils.excel.excel_exporter.dirname')
    def test_get_workbook__file_does_not_exist__create_if_doesnt_exist(self, dirname, makedirs):
        excel_exporter = ExcelExporter(Mock())
        file_path = Mock()

        # Directory with the same path exists
        self.exists.return_value = True
        self.isfile.return_value = False

        write_mode = WriteMode.CREATE_IF_DOESNT_EXIST
        excel_exporter.get_workbook(file_path, write_mode)
        dirname.assert_called_once_with(file_path)
        makedirs.assert_called_once()

    @patch('qf_lib.documents_utils.excel.excel_exporter.Workbook')
    def test_get_workbook__file_does_not_exist__create(self, workbook):
        excel_exporter = ExcelExporter(Mock())
        file_path = Mock()

        # Directory with the same path exists
        self.exists.return_value = False
        self.isfile.return_value = False

        write_mode = WriteMode.CREATE
        excel_exporter.get_workbook(file_path, write_mode)
        workbook.assert_called_once()

    def test_get_worksheet(self):
        workbook = MagicMock()
        excel_exporter = ExcelExporter(Mock())

        self.assertEqual(excel_exporter.get_worksheet(workbook), workbook.active)

        work_sheet = workbook["Sheet name"]
        workbook.__contains__.side_effect = lambda name: name == "Sheet name"
        self.assertEqual(excel_exporter.get_worksheet(workbook, "Sheet name"), work_sheet)

        self.assertNotEqual(excel_exporter.get_worksheet(workbook, "Sheet name 2"), work_sheet)
        workbook.create_sheet.assert_called_once_with("Sheet name 2")

    def test_write_to_worksheet__export_series_with_index(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFSeries(data=[12, 34], index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 2, 3, True, False)
        calls = [
            {"row": 2, "column": 3, "value": 100},
            {"row": 2, "column": 4, "value": 12},
            {"row": 3, "column": 3, "value": 101},
            {"row": 3, "column": 4, "value": 34},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_named_series_with_index(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFSeries(data=[12, 34], index=[100, 101])
        series.name = "Magic trick"

        excel_exporter.write_to_worksheet(series, worksheet, 2, 3, True, True)
        calls = [
            {"row": 2, "column": 3, "value": "Index"},
            {"row": 2, "column": 4, "value": "Magic trick"},
            {"row": 3, "column": 3, "value": 100},
            {"row": 3, "column": 4, "value": 12},
            {"row": 4, "column": 3, "value": 101},
            {"row": 4, "column": 4, "value": 34},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_series_without_index(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFSeries(data=[12, 34], index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 2, 3, False, False)
        calls = [
            {"row": 2, "column": 3, "value": 12},
            {"row": 3, "column": 3, "value": 34},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_named_series_without_index(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFSeries(data=[12, 34], index=[100, 101])
        series.name = "Magic trick"

        excel_exporter.write_to_worksheet(series, worksheet, 2, 3, False, True)
        calls = [
            {"row": 2, "column": 3, "value": "Magic trick"},
            {"row": 3, "column": 3, "value": 12},
            {"row": 4, "column": 3, "value": 34},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_tickers_series_without_index(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFSeries(data=[BloombergTicker("ABC"), BloombergTicker("DEF")], index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 2, 3, False, False)
        calls = [
            {"row": 2, "column": 3, "value": "ABC"},
            {"row": 3, "column": 3, "value": "DEF"},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_dataframe_with_index_and_column_names(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFDataFrame(data={"A": [12, 34], "B": [BloombergTicker("ABC"), BloombergTicker("DEF")]},
                             index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 2, 3, True, True)
        calls = [
            {"row": 2, "column": 3, "value": "Index"},
            {"row": 2, "column": 4, "value": "A"},
            {"row": 2, "column": 5, "value": "B"},
            {"row": 3, "column": 3, "value": 100},
            {"row": 3, "column": 4, "value": 12},
            {"row": 3, "column": 5, "value": "ABC"},
            {"row": 4, "column": 3, "value": 101},
            {"row": 4, "column": 4, "value": 34},
            {"row": 4, "column": 5, "value": "DEF"},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_dataframe_without_index_with_column_names(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFDataFrame(data={"A": [12, 34], "B": [BloombergTicker("ABC"), BloombergTicker("DEF")]},
                             index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 2, 4, False, True)
        calls = [
            {"row": 2, "column": 4, "value": "A"},
            {"row": 2, "column": 5, "value": "B"},
            {"row": 3, "column": 4, "value": 12},
            {"row": 3, "column": 5, "value": "ABC"},
            {"row": 4, "column": 4, "value": 34},
            {"row": 4, "column": 5, "value": "DEF"},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_dataframe_without_index_and_column_names(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFDataFrame(data={"A": [12, 34], "B": [BloombergTicker("ABC"), BloombergTicker("DEF")]},
                             index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 3, 4, False, False)
        calls = [
            {"row": 3, "column": 4, "value": 12},
            {"row": 3, "column": 5, "value": "ABC"},
            {"row": 4, "column": 4, "value": 34},
            {"row": 4, "column": 5, "value": "DEF"},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_to_worksheet__export_dataframe_with_index_without_column_names(self):
        excel_exporter = ExcelExporter(Mock())

        worksheet = Mock()
        series = QFDataFrame(data={"A": [12, 34], "B": [BloombergTicker("ABC"), BloombergTicker("DEF")]},
                             index=[100, 101])

        excel_exporter.write_to_worksheet(series, worksheet, 3, 3, True, False)
        calls = [

            {"row": 3, "column": 3, "value": 100},
            {"row": 3, "column": 4, "value": 12},
            {"row": 3, "column": 5, "value": "ABC"},
            {"row": 4, "column": 3, "value": 101},
            {"row": 4, "column": 4, "value": 34},
            {"row": 4, "column": 5, "value": "DEF"},
        ]
        worksheet.cell.assert_has_calls([call(**c) for c in calls], any_order=True)

    def test_write_cell(self):
        excel_exporter = ExcelExporter(Mock())
        workbook = MagicMock()
        worksheet = MagicMock()
        workbook.create_sheet.return_value = worksheet

        self.exists.return_value = True
        self.isfile.return_value = True
        self.load_workbook.return_value = workbook

        excel_exporter.write_cell(Mock(), "B3", 17, WriteMode.CREATE_IF_DOESNT_EXIST, "New sheet")

        worksheet.cell.assert_called_once_with(row=3, column=2, value=17)
