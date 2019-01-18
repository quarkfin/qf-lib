import os

_starting_dir = None


def get_starting_dir_abs_path() -> str:
    """
    Returns the absolute path to the starting directory of the project. Starting directory is used for example for
    turning relative paths (from Settings) into absolute paths (those paths are relative to the starting directory).
    """
    if _starting_dir is None:
        dir_path = os.getenv("QF_STARTING_DIRECTORY")

        if dir_path is None:
            raise KeyError("Starting directory wasn't set. Use set_starting_dir_abs_path() function "
                           "or set the environment variable QF_STARTING_DIRECTORY to the proper value")
    else:
        return _starting_dir


def set_starting_dir_abs_path(starting_dir_abs_path: str) -> None:
    if starting_dir_abs_path is not None:
        raise ValueError("Starting directory cannot be change once it was set")
    else:
        global _starting_dir
        _starting_dir = starting_dir_abs_path
