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
            return dir_path
    else:
        return _starting_dir


def set_starting_dir_abs_path(starting_dir_abs_path: str) -> None:
    """Sets the starting directory, which is used by a number of classes to e.g. output files to a designated directory.

    Parameters
    ----------
    starting_dir_abs_path: str
        Absolute path to the top directory of the project.
    """
    global _starting_dir
    if _starting_dir is not None:
        raise ValueError("Starting directory cannot be change once it was set")
    else:
        _starting_dir = starting_dir_abs_path
