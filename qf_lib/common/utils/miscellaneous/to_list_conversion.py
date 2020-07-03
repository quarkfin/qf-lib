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

from typing import Union, Sequence, Tuple, Type, TypeVar

SingleValueT = TypeVar('SingleValueT')


def convert_to_list(
        value: Union[SingleValueT, Sequence[SingleValueT]],
        type_of_single_value: Union[Type[SingleValueT], Sequence[Type[SingleValueT]]]) \
        -> Tuple[Sequence[SingleValueT], bool]:
    """
    Converts a given value to list if necessary and returns information if the conversion was necessary.

    Parameters
    ----------
    value
        value or sequence of values to be converted
    type_of_single_value
        allowed type (or types) of a single value of the element which should be converted to list

    Returns
    -------
    List, bool
        a list of values and a bool value indicating whether the convertion was necessary (True) or not (False)
    """
    if isinstance(value, type_of_single_value):
        list_of_values = [value]
        was_convertion_necessary = True
    elif isinstance(value, Sequence):
        list_of_values = value
        was_convertion_necessary = False
    else:
        raise ValueError("Incorrect type of an argument.")

    return list_of_values, was_convertion_necessary
