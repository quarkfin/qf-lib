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

from typing import List


def generate_sample_column_names(num_of_columns: int) -> List[str]:
    """
    Generates columns' names like a, b, c, ...
    """
    regressors_names = []
    for i in range(ord('a'), ord('a') + num_of_columns):
        regressors_names.append(chr(i))

    return regressors_names
