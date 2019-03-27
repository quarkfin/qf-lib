from math import sqrt
from typing import Union, List

from pandas import Series

from qf_lib.common.enums.frequency import Frequency


def annualise_with_sqrt(values: Union[float, Series, List[float]], frequency: Frequency) \
        -> Union[float, Series, List[float]]:
    """
    Annualises samples of given frequency by multiplying each value by the square-rooted number of samples in a year
    for a given frequency.

    Parameters
    ----------
    values
        value(s) to annualise
    frequency
        original sampling frequency for the given value(s)

    Returns
    -------
    annualised_values
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
