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

from pandas import DataFrame

from qf_lib.common.enums.frequency import Frequency
from qf_lib.documents_utils.excel.excel_importer import ExcelImporter
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.prices_series import PricesSeries


def import_data(frequency: Frequency, file_path: str):
    xlsx = ExcelImporter()
    df = xlsx.import_container(
        file_path, 'A1', 'J1888', sheet_name="Data", include_index=True, include_column_names=True)
    weights = xlsx.import_container(
        file_path, 'M15', 'N23', sheet_name="Data", include_index=True, include_column_names=False)

    simple_ret_df = DataFrame()
    for column in df:
        prices = PricesSeries(df[column])
        simple_returns = get_aggregate_returns(prices, frequency)
        simple_ret_df[column] = simple_returns

    return simple_ret_df, weights
