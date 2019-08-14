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


def iso_to_gregorian(iso_year: int, iso_week: int, iso_day: int):
    """
    Gregorian calendar date for the given ISO year, week and day.

    Taken from: http://stackoverflow.com/a/33101215/492186.

    Parameters
    ----------
    iso_year
    iso_week
        From 1 to 53.
    iso_day
        From 1 to 7.

    Returns
    -------
    date
    """
    fourth_jan = datetime.date(iso_year, 1, 4)
    _, fourth_jan_week, fourth_jan_day = fourth_jan.isocalendar()
    return fourth_jan + datetime.timedelta(days=iso_day - fourth_jan_day, weeks=iso_week - fourth_jan_week)
