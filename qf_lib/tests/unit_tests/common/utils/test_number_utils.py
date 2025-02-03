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
import pytest
from numpy.testing import assert_almost_equal

from qf_lib.common.utils.numberutils.norm_fit import norm_fit
from qf_lib.common.utils.numberutils.probability_density_function import probability_density_function
from qf_lib.containers.series.qf_series import QFSeries


@pytest.mark.parametrize(
    "x, loc, scale, expected_value",
    [
        (20, 20, 20, 0.019947114020071637),
        (20, 20, 10, 0.039894228040143274),
        (15, 20, 10, 0.03520653267642995),
        (10, 15, 10, 0.03520653267642995),
        (10, 20, 10, 0.02419707245191434),
        (10, 15, 20, 0.019333405840142464),

    ]
)
def test_probability_density_function(x, loc, scale, expected_value):
    assert_almost_equal(probability_density_function(x, loc, scale), expected_value, decimal=6)


@pytest.mark.parametrize(
    "data, expected_value",
    [
        (QFSeries([10, 15, 20, 25, 30]), (20, 7.0710678118654755)),
        (QFSeries([10, 15, 10, 5, 10]), (10, 3.1622776601683795)),
        (QFSeries([1, 3, 5, 7, 9]), (5, 2.8284271247461903)),
        (QFSeries([21, 56, 21, 98, 34, 9, 34, 78, 23]), (41.555555, 28.059900653625952))

    ]
)
def test_norm_fit(data, expected_value):
    print(norm_fit(data))
    assert_almost_equal(norm_fit(data), expected_value, decimal=6)
