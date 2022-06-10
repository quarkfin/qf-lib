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

from enum import Enum


class DateFormat(Enum):
    """
    Class defining date formats (as strings).
    """
    ISO = "%Y-%m-%d"
    """YYYY-MM-DD"""

    YEAR_DOT_MONTH = "%Y.%m"
    """YYYY.MM"""

    YEAR_DOT_MONTH_DOT_DAY = "%Y.%m.%d"
    """YYYY.MM.DD"""

    ISO_MINUTES = "%Y-%m-%d %H_%M"
    """YYYY-MM-DD HH_MM"""

    ISO_SECONDS = "%Y-%m-%d %H_%M_%S"
    """YYYY-MM-DD HH_MM_SS"""

    FULL_ISO = "%Y-%m-%d %H:%M:%S.%f"
    """YYYY-MM-DD HH:MM:SS.ffffff (ffffff - microseconds)"""

    LONG_DATE = "%d %B %Y"
    """DD Mmmm YYYY (e.g. 03 March 2017)"""

    def __init__(self, format_string):
        self.format_string = format_string

    def __str__(self):
        return self.value
