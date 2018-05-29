from typing import Union, Sequence, Tuple, Type, TypeVar

SingleValueT = TypeVar('SingleValueT')


def convert_to_list(
    value: Union[SingleValueT, Sequence[SingleValueT]],
    type_of_single_value: Union[Type[SingleValueT], Sequence[Type[SingleValueT]]]
) -> Tuple[Sequence[SingleValueT], bool]:
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
    a list of values
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
