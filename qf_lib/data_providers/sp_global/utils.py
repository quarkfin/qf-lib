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
from functools import wraps
from qf_lib.common.utils.helpers import grouper


def fetch_in_chunks(arg_name: str, chunk_size: int = 1000):
    """
    Utility decorator, which takes a function and a given argument (identified by arg_name) representing a list,
    divides the list into chunks of the given size (chunk_size), executes the wrapped function separately for each
    chunk and returns the result for each chunk in form of a list.

    Parameters
    ----------
    arg_name: str
        The name of the parameter passed to the wrapped function, which should be divided into chunks. Must be of
        list type.
    chunk_size: int
        The size of the chunks
    """
    def decorator(fetch_func):
        @wraps(fetch_func)
        def wrapper(*args, **kwargs):
            # Extract all the arguments and search the one by which the query should be grouped
            arg_dict = dict(zip(fetch_func.__code__.co_varnames, args))
            target_list = arg_dict.get(arg_name) or kwargs.get(arg_name)
            if target_list is None:
                raise ValueError(f"The argument '{arg_name}' is not a valid parameter of {fetch_func.__name__}.")
            if not isinstance(target_list, list):
                raise ValueError(f"The argument '{arg_name}' must be a list.")

            # Expecting identifiers to be the first argument
            results = []
            for group in grouper(chunk_size, target_list):
                new_args = list(args)
                if arg_name in arg_dict:
                    index = fetch_func.__code__.co_varnames.index(arg_name)
                    new_args[index] = group
                else:
                    kwargs[arg_name] = group

                results.append(fetch_func(*new_args, **kwargs))
            return results
        return wrapper
    return decorator
