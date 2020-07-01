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


def date_to_str(date: datetime.datetime, date_format: DateFormat = DateFormat.ISO) -> str:
    """
    Converts date object into string.

    Parameters
    ----------
    date
        date to be converted to string
    date_format
        date format of the output string

    Returns
    -------
    string
        representation of a given date
    """

    return date.strftime(date_format.format_string)
