import os
from os.path import join

from qf_common.config.ioc import container
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.settings import Settings

settings = container.resolve(Settings)

xlx_file_path = join(settings.output_directory, 'excel_example.xlsx')
# Make sure an old version of this file is removed.
if os.path.exists(xlx_file_path):
    os.remove(xlx_file_path)

xlx_exporter = ExcelExporter(settings)
df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
xlx_exporter.export_container(df, xlx_file_path, starting_cell='C10', include_column_names=True)

xlx_exporter.write_cell(xlx_file_path, "D9", "Some random title")
