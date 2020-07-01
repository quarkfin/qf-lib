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

from typing import List

from qf_lib.containers.time_indexed_container import TimeIndexedContainer


def get_values_for_common_dates(*containers: TimeIndexedContainer, remove_nans: bool = False)\
        -> List[TimeIndexedContainer]:
    """
    Gets list/tuple of series/dataframes (possibly mixed) and finds the common dates for all of them. Then it returns
    corresponding series/dataframes as a list. All series and dataframes in the result list contain only values
    for common dates.

    Parameters
    ----------
    containers
        variable length list of arguments where each of the arguments is a TimeIndexedContainer
    remove_nans
        if True, then all incomplete rows will be removed from each provided container before finding common dates

    Returns
    -------
    List
        list composed of TimeIndexedContainers containing only values for common dates
    """
    if remove_nans:
        dates_axis_number = 0
        containers = [container.dropna(axis=dates_axis_number) for container in containers]

    common_dates = containers[0].index

    for i in range(1, len(containers)):
        container = containers[i]
        common_dates = common_dates.intersection(container.index)

    return [container.loc[common_dates] for container in containers]
