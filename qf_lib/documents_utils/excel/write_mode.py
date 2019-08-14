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


class WriteMode(Enum):
    """
    Class defining the access modes for writing to the file.
    """

    OPEN_EXISTING = 0           # open the file if it exists; if it doesn't, raise an error
    CREATE = 1                  # create a new file; if it does exist, raise an error
    CREATE_IF_DOESNT_EXIST = 2  # create a new file, if it doesn't exist; open an existing one if it does
