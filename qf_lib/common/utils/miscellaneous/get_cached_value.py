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

import pickle
from os.path import exists
from typing import Any, Callable

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class CachedValueException(Exception):
    pass


def cached_value(func: Callable[[], Any], path) -> Any:
    """
    Tries to load data from the pickle file. If the file doesn't exist, the func() method is run and its results
    are saved into the file. Then the result is returned.
    """

    if exists(path):
        with open(path, 'rb') as file:
            result = pickle.load(file)
    else:
        try:
            result = func()
            with open(path, 'wb') as file:
                pickle.dump(result, file, protocol=3)

        except CachedValueException:
            logger = qf_logger.getChild(__name__)
            logger.error('Error while processing {}'.format(func))

    return result
