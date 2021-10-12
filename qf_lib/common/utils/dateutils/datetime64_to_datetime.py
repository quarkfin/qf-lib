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
import datetime

from numpy import datetime64, timedelta64


def datetime64_to_datetime(np_datetime64: datetime64) -> datetime.datetime:
    """
    Converts numpy datetime64 object to the python datetime.

    Parameters
    ----------
    np_datetime64
        datetime in the numpy datetime64 format

    Returns
    -------
    datetime
        python datetime object
    """

    return datetime.datetime.utcfromtimestamp((np_datetime64 - datetime64(0, 's')) / timedelta64(1, 's'))
