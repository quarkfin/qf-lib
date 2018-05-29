import numpy as np


def log_to_simple_return(log_return: float) -> float:
    """
    Converts logarithmic return to corresponding simple return

    Parameters
    ----------
    log_return: float

    Returns
    -------
    simple_return: float
        logarithmic return
    """

    simple_return = np.exp(log_return) - 1
    return simple_return
