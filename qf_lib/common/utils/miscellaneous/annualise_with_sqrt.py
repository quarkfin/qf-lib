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

from math import sqrt
from typing import Union, List

from pandas import Series

from qf_lib.common.enums.frequency import Frequency


def annualise_with_sqrt(
        values: Union[float, Series, List[float]], frequency: Frequency) -> Union[float, Series, List[float]]:
    """
    Annualises samples of given frequency by multiplying each value by the square-rooted number of samples in a year
    for a given frequency.

    Parameters
    ----------
    values: float, Series, List[float]
        value(s) to annualise
    frequency: Frequency
        original sampling frequency for the given value(s)

    Returns
    -------
    loat, Series, List[float]
        annualised values
    """

    occurrences_in_year = frequency.occurrences_in_year

    if isinstance(values, float) or isinstance(values, int):
        annualised_values = values * sqrt(occurrences_in_year)
    elif isinstance(values, Series):
        annualised_values = values.multiply(sqrt(occurrences_in_year))
    else:
        annualised_values = [value * sqrt(occurrences_in_year) for value in values]

    return annualised_values
