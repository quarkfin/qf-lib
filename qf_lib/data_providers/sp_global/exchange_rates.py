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


class SPExchangeRate(Enum):
    """ Enum with all available exchange rate snapshots, used by S&P Global. """
    SydneyMidday = 1
    TokyoMidday = 2
    SydneyClose = 3
    TokyoClose = 4
    LondonMidday = 5
    LondonClose = 6
    NewYorkMidday = 7
    NewYorkClose = 8
