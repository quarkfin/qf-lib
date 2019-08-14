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

import numbers

import numpy as np


def is_finite_number(variable) -> bool:
    """
    Checks if the given variable is number and if it is finite.

    Parameters
    ----------
    variable
        variable to be tested

    Returns
    -------
    is_finite_number: bool
        True if the variable is the finite number, False otherwise

    """
    return variable is not None and isinstance(variable, numbers.Number) and np.isfinite(variable)
