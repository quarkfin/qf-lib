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

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


def main():
    xlx_file_path = 'excel_example.xlsx'
    xlx_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter

    df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
    absolute_path = xlx_exporter.export_container(
        df, xlx_file_path, starting_cell='C10', include_column_names=True, remove_old_file=True)

    xlx_exporter.write_cell(absolute_path, "D9", "Some random title")

    print("Saved data to {}".format(absolute_path))


if __name__ == '__main__':
    main()
