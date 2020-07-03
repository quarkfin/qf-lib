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

from pandas import Timedelta


def to_days(timedelta: Timedelta) -> float:
    """
    Converts Timedelta variable into number of days (expressed as float).

    Parameters
    ----------
    timedelta: Timedelta
        pandas Timedelta value

    Returns
    -------
    float
        number of days that corresponds to the given time delta
    """

    return timedelta / Timedelta('1 days')
