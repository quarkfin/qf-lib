from math import sqrt

from qf_lib.common.enums.frequency import Frequency


def annualise_with_sqrt(values, frequency: Frequency) -> float:
    """
    Annualises samples of given frequency by multiplying each value by the square-rooted number of samples in a year
    for a given frequency.

    Parameters
    ----------
    values : float/List[float]
        value(s) to annualise
    frequency : Frequency
        original sampling frequency for the given value(s)

    Returns
    -------
    annualised_values : float/List[float]
        annualised values
    """

    is_scalar = isinstance(values, float) or isinstance(values, int)
    occurrences_in_year = frequency.occurrences_in_year

    if is_scalar:
        annualised_values = values * sqrt(occurrences_in_year)
    else:
        annualised_values = [value * sqrt(occurrences_in_year) for value in values]

    return annualised_values
