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


class Aggregation(Enum):
    """
    List of aggregations used for reporting.
    """

    TOTAL_PORTFOLIO = "Total"

    ASIA_EQUITY = "Asia Equity"
    EM_EQUITY = "EM Equity"
    EUROPE_EQUITY = "Europe Equity"
    INTERNAL_EQUITY = "Internal Equity"
    NORTH_AMERICA_EQUITY = "North America Equity"

    def __init__(self, short_description: str):
        self.short_description = short_description
