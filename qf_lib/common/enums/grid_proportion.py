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


class GridProportion(Enum):
    One = "one"
    Two = "two"
    Three = "three"
    Four = "four"
    Five = "five"
    Six = "six"
    Seven = "seven"
    Eight = "eight"
    Nine = "nine"
    Ten = "ten"
    Eleven = "eleven"
    Twelve = "twelve"
    Thirteen = "thirteen"
    Fourteen = "fourteen"
    Fifteen = "fifteen"
    Sixteen = "sixteen"

    def __str__(self):
        return self.value

    def to_int(self) -> int:
        mapping = {
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5,
            'six': 6,
            'seven': 7,
            'eight': 8,
            'nine': 9,
            'ten': 10,
            'eleven': 11,
            'twelve': 12,
            'thirteen': 13,
            'fourteen': 14,
            'fifteen': 15,
            'sixteen': 16
        }
        return mapping[self.value]
