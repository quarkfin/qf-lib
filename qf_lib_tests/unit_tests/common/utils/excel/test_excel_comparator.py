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

from shutil import copyfile

from os.path import join, dirname

from qf_lib.documents_utils.excel.excel_files_comparator import ExcelFilesComparator
from qf_lib_tests.helpers.testing_tools.test_case import TestCaseWithFileOutput
from qf_lib_tests.unit_tests.common.utils.excel.constants import SINGLE_SHEET_ONE_SERIES, SINGLE_SHEET_ONE_SERIES_2


class TestExcelComparator(TestCaseWithFileOutput):
    _tmp_dir = join(dirname(__file__), 'tmp')
    _templates_dir = join(dirname(__file__), 'dummies')
    comparator = ExcelFilesComparator()
    file_path_1 = join(_tmp_dir, '1.xlsx')
    file_path_2 = join(_tmp_dir, '2.xlsx')

    def setUp(self):
        first_file_path = join(self._templates_dir, SINGLE_SHEET_ONE_SERIES)
        second_file_path = join(self._templates_dir, SINGLE_SHEET_ONE_SERIES_2)

        copyfile(first_file_path, self.file_path_1)
        copyfile(second_file_path, self.file_path_2)

    def tearDown(self):
        self.clear_tmp_dir()

    def tmp_dir(self):
        return self._tmp_dir

    def templates_dir(self):
        return self._templates_dir

    def test_comparing_two_files(self):
        self.comparator.assert_the_same(self.file_path_1, self.file_path_2)
