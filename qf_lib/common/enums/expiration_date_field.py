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
from typing import List


class ExpirationDateField(Enum):
    """
    Enumeration representing different expiration dates for futures contracts.
    """

    FirstNotice = 1
    """Futures First Notice date"""

    LastTradeableDate = 2
    """Futures Last Tradeable date"""

    @staticmethod
    def all_dates() -> List:
        """

        Returns
        -------
        List
            list of all dates types
        """
        return [ExpirationDateField.FirstNotice, ExpirationDateField.LastTradeableDate]
