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


class Location(Enum):
    BEST = 0
    UPPER_RIGHT = 1
    UPPER_LEFT = 2
    LOWER_LEFT = 3
    LOWER_RIGHT = 4
    RIGHT = 5
    CENTER_LEFT = 6
    CENTER_RIGHT = 7
    LOWER_CENTER = 8
    UPPER_CENTER = 9
    CENTER = 10

    def __init__(self, code):
        self.code = code


class AxisLocation(Enum):
    """
    Custom location for legend placements. In axis lengths for placement.
    e.g (1,0) = (x=1, y=0) = BOTTOM_RIGHT
    """
    LOWER_RIGHT = (1, 0)
    LOWER_LEFT = (0, 0)
    UPPER_RIGHT = (1, 1)
    UPPER_LEFT = (0, 1)
