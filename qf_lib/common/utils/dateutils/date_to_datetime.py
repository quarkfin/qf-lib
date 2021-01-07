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


def date_to_datetime(date: datetime.date) -> datetime.datetime:
    """
    Converts date into datetime object.

    Parameters
    ----------
    date
        date which should be converted into datetimne

    Returns
    -------
    datetime
        object representing datetime
    """

    return datetime.datetime(date.year, date.month, date.day)
