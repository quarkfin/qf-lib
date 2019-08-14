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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame


def convert_dataframe_frequency(dataframe: QFDataFrame, frequency: Frequency) -> SimpleReturnsDataFrame:
    """
    Converts each column in the dataframe to the specified frequency.
    ValueError is raised when a column has a lower frequency than the one we are converting to.
    """
    # Verify that all columns in the dataframe have a lower frequency.
    data_frequencies = dataframe.get_frequency()
    for column, col_frequency in data_frequencies.items():
        if col_frequency < frequency:
            raise ValueError("Column '{}' cannot be converted to '{}' frequency because its frequency is '{}'.".format(
                column, frequency, col_frequency))

    if frequency == Frequency.DAILY:
        return dataframe.to_simple_returns()

    filled_df = dataframe.to_prices().fillna(method="ffill")
    new_columns = {}
    for column in filled_df:
        new_columns[column] = get_aggregate_returns(filled_df[column], frequency)

    return SimpleReturnsDataFrame(new_columns)
