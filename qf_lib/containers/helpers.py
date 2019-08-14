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

from typing import Sequence, Any


def rolling_window_slices(index: Sequence[Any], size: Any, step: int = 1) -> Sequence[slice]:
    slices = []
    last_idx_value = index[-1]

    start_indices = [idx for i, idx in enumerate(index) if i % step == 0]

    for idx in start_indices:
        start_idx = idx
        end_idx = start_idx + size

        if end_idx < last_idx_value:
            slices.append(slice(start_idx, end_idx))
        else:
            slices.append(slice(start_idx, last_idx_value))
            break

    return slices
