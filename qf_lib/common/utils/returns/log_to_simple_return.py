import numpy as np


def log_to_simple_return(log_return: float) -> float:
    """
    Converts logarithmic return to corresponding simple return.

    Parameters
    ----------
    log_return
        logarithmic return

    Returns
    -------
    simple_return
        simple return

    """

    simple_return = np.exp(log_return) - 1
    return simple_return
