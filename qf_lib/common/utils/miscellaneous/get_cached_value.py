import os
import pickle
from typing import Any, Callable


def cached_value(func: Callable[[], Any], path) -> Any:
    """
    Tries to load data from the pickle file. If the file doesn't exist, the func() method is run and its results
    are saved into the file. Then the result is returned.
    """

    if os.path.exists(path):
        with open(path, 'rb') as file:
            result = pickle.load(file)
    else:
        result = func()
        with open(path, 'wb') as file:
            pickle.dump(result, file)

    return result
