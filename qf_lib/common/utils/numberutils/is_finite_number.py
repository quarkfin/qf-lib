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
