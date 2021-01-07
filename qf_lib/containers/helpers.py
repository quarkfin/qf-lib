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
import hashlib
from typing import Union

from pandas.core.util.hashing import hash_pandas_object

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries


def compute_container_hash(data_container: Union[QFSeries, QFDataFrame, QFDataArray]) -> str:
    """
    For the given data container returns the hexadecimal digest of the data.

    Parameters
    ----------
    data_container: QFSeries, QFDataFrame, QFDataArray
        container, which digest should be computed

    Returns
    -------
    str
        hexadecimal digest of data in the passed data container
    """
    if isinstance(data_container, QFSeries):
        hashed_container = hash_pandas_object(data_container)

    elif isinstance(data_container, QFDataFrame):
        hashed_container = hash_pandas_object(data_container)

    elif isinstance(data_container, QFDataArray):
        hash_data_frame = QFDataFrame([hash_pandas_object(data_container.loc[:, :, field].to_pandas())
                                       for field in data_container.fields])
        hashed_container = hash_pandas_object(hash_data_frame)
    else:
        raise ValueError("Unsupported type of data container")

    return hashlib.sha1(hashed_container.values).hexdigest()


def get_containers_for_common_dates(container1, container2):
    common_dates = container1.index.intersection(container2.index)

    def crop_results(container):
        if isinstance(container, QFSeries):
            result = container.loc[common_dates]
        elif isinstance(container, QFDataFrame):
            result = container.loc[common_dates, :]
        else:
            raise ValueError("container has to be a QFSeries or a QFDataFrame")
        return result

    container1_result = crop_results(container1)
    container2_result = crop_results(container2)

    return container1_result, container2_result
