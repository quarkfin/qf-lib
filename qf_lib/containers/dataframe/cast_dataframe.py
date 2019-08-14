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


def cast_dataframe(dataframe: DataFrame, output_type: type):
    """
    Casts the given dataframe to another dataframe type specified by output_type (e.g. casts container of type
    pd.DataFrame to QFDataFrame).

    Parameters
    ----------
    dataframe
        dataframe to be casted
    output_type
        type to which dataframe should be casted

    Returns
    -------
    casted_dataframe
        new dataframe of given type
    """
    return output_type(data=dataframe.values, index=dataframe.index, columns=dataframe.columns).__finalize__(dataframe)
