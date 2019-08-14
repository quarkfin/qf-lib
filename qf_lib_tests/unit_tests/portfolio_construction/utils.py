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

from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.documents_utils.excel.excel_importer import ExcelImporter


def _get_assets_df():
    input_data_path = join(dirname(__file__), 'test_data.xlsx')
    excel_importer = ExcelImporter()
    return excel_importer.import_container(input_data_path, 'A2', 'U505', SimpleReturnsDataFrame)


assets_df = _get_assets_df()
