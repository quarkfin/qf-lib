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
import math
from typing import Sequence


def norm_fit(data: Sequence):
    """Estimate the parameters (mu, sigma) of a normal distribution given data."""
    n = len(data)
    if n == 0:
        raise ValueError("Data must contain at least one value")

    mu = sum(data) / n
    # Maximum likelihood estimation of variance
    variance = sum((x - mu) ** 2 for x in data) / n
    sigma = math.sqrt(variance)
    return mu, sigma
