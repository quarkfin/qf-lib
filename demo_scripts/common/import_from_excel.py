from pandas import DataFrame

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.excel.excel_importer import ExcelImporter
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.prices_series import PricesSeries


def import_data(frequency: Frequency, file_path:str):
    xlsx = ExcelImporter()
    df = xlsx.import_container(file_path, 'A1', 'J1888', sheet_name="Data", include_index=True, include_column_names=True)
    weights = xlsx.import_container(file_path, 'M15', 'N23', sheet_name="Data", include_index=True, include_column_names=False)

    simple_ret_df = DataFrame()
    for column in df:
        prices = PricesSeries(df[column])
        simple_returns = get_aggregate_returns(prices, frequency)
        simple_ret_df[column] = simple_returns

    return simple_ret_df, weights
