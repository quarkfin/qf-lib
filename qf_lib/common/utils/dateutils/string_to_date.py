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

from qf_lib.common.utils.dateutils.date_format import DateFormat


def str_to_date(string_date: str, date_format: DateFormat = DateFormat.ISO) -> datetime.datetime:
    """
    Converts string into date object.

    Parameters
    ----------
    string_date
        date encoded in the string
    date_format
        format of the date passed as a string

    Returns
    -------
    date
        object representing date
    """

    return datetime.datetime.strptime(string_date, date_format.value)
