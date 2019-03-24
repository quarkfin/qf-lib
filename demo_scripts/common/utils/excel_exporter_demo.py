from qf_common.config.ioc import container
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.settings import Settings

xlx_file_path = 'excel_example.xlsx'

settings = container.resolve(Settings)
xlx_exporter = ExcelExporter(settings)

df = QFDataFrame({"Test": [1, 2, 3, 4, 5], "Test2": [10, 20, 30, 40, 50]}, ["A", "B", "C", "D", "E"])
xlx_exporter.export_container(df, xlx_file_path, starting_cell='C10', include_column_names=True, remove_old_file=True)

xlx_exporter.write_cell(xlx_file_path, "D9", "Some random title")
