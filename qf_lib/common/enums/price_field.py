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


class PriceField(Enum):
    """
    Represents one of the data fields that corresponds to OHLC and Volume.
    """

    Open = 1
    """Open Price"""
    High = 2
    """High Price"""
    Low = 3
    """Low Price"""
    Close = 4
    """Close Price"""
    Volume = 5
    """Volume"""

    @staticmethod
    def ohlcv() -> List["PriceField"]:
        """Return a list of all possible price field values.

        Returns
        -------
        List[PriceField]
            list of all price field values
        """
        return [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume]

    @staticmethod
    def ohlc() -> List["PriceField"]:
        """Return a list of all possible price field values.

        Returns
        -------
        List[PriceField]
            list of all price field values
        """
        return [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]

    def __lt__(self, other):
        if not isinstance(other, PriceField):
            raise TypeError("Cannot compare this object with a PriceField")

        return self.value < other.value
