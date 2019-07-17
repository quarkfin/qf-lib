import numpy as np


def simple_to_log_return(simple_return: float) -> float:
    """
    Converts simple return to the corresponding logarithmic return.

    Parameters
    ----------
    simple_return
        simple return

    Returns
    -------
    log_return
        logarithmic return
    """

    log_return = np.log(1 + simple_return)
    return log_return
