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

from datetime import datetime
from typing import Tuple

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.time_indexed_container import TimeIndexedContainer


def get_common_start_and_end(*containers: TimeIndexedContainer) -> Tuple[datetime, datetime]:
    """
    Finds the first and last valid dates (with a value different than NaN) for each column and then returns the latest
    of starting dates and the soonest ending date.

    If one of containers is dataframe then it is split into separate columns first.

    Parameters
    ----------
    containers
        list of containers for which the common beginning and ending should be found

    Returns
    -------
    Tuple[datetime, datetime]
        (common_start, common_end) - (soonest date on which data for all series is already available, latest date on
        which data for all series is still available)
    """
    start_dates = []
    end_dates = []
    for container in containers:
        if isinstance(container, QFDataFrame):
            start_date = container.apply(lambda col: col.first_valid_index()).max()
            start_dates.append(start_date)

            end_date = container.apply(lambda col: col.last_valid_index()).min()
            end_dates.append(end_date)
        else:
            start_dates.append(container.first_valid_index())
            end_dates.append(container.last_valid_index())

    common_start = max(start_dates)
    common_end = min(end_dates)

    return common_start, common_end
