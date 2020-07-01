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

import calendar
from datetime import datetime


def eom_date(date: datetime = None, year: int = None, month: int = None) -> datetime:
    """
    Tells what is the last date of the month for given date or for given year and a month.

    Parameters
    ----------
    date
        date for which the corresponding last date of the month should be returned
    year
        year containing the month for which last date of the month should be returned
    month
        number of month (1 -> January, 2-> February, ...) for which the last date of the month will be returned

    Returns
    -------
    datetime
        last date of the month for given date
    """
    if date is not None:
        assert year is None and month is None
        year = date.year
        month = date.month
    else:
        assert year is not None and month is not None

    weekday, last_day_in_month = calendar.monthrange(year, month)
    return datetime(year, month, last_day_in_month)
