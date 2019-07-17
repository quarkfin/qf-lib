from os.path import dirname, join

from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.documents_utils.excel.excel_importer import ExcelImporter


def _get_assets_df():
    input_data_path = join(dirname(__file__), 'test_data.xlsx')
    excel_importer = ExcelImporter()
    return excel_importer.import_container(input_data_path, 'A2', 'U505', SimpleReturnsDataFrame)


assets_df = _get_assets_df()
