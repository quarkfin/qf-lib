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


def probability_density_function(x, mu: float = 0, sigma: float = 1):
    """
    Compute the probability density function (PDF) of a normal distribution.
    Defined in the standardized form, analogically to scipy.stats.norm.pdf.
    To shift and scale the distribution loc and scale parameters should be used.
    """
    coefficient = 1 / (sigma * math.sqrt(2 * math.pi))
    exponent = math.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    return coefficient * exponent
