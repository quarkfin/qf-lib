from typing import Sequence, TypeVar, List

import numpy as np
import pandas as pd

from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number

T = TypeVar('T')


def assert_lists_equal(expected_list: Sequence[T], actual_list: Sequence[T],
                       absolute_tolerance: float = 1e-4, relative_tolerance: float = 0.0) -> None:
    """
    Checks if two lists (or tuples) are the same. If they aren't, the AssertionError is raised.
    If data is numeric then the values can be different to some extent.
    Tthey're considered the same if the following condition is satisfied:
        abs(actual_value - expected_value) <= absolute_tolerance + relative_tolerance * abs(expected_value).

    Parameters
    ----------
    expected_list
        expected list of values
    actual_list
        actual list of values
    absolute_tolerance
        see: description of the method
    relative_tolerance
        see: description of the method

    Raises
    -------
    ex: AssertionError
        exception thrown when two lists are not equal
    """
    expected_list_length = len(expected_list)
    actual_list_length = len(actual_list)
    assert expected_list_length == actual_list_length, \
        "Different lengths of lists. Expected: {:d}, got {:d}".format(expected_list_length, actual_list_length)

    different_vals = []  # type: List[str]
    for i, (expected_val, actual_val) in enumerate(zip(expected_list, actual_list)):
        if _two_values_are_different(expected_val, actual_val, absolute_tolerance, relative_tolerance):
            different_vals.append("{:<7d}   {:25s}   {:25s}".format(i, str(expected_val), str(actual_val)))

    if different_vals:
        different_vals = ["\n{:7s}   {:25s}   {:25s}".format("Index", "Expected", "Actual")] + different_vals
        raise AssertionError("\n".join(different_vals))


def _two_values_are_different(expected_val, actual_val, absolute_tolerance, relative_tolerance):
    if is_finite_number(expected_val):
        return _two_numbers_are_different(expected_val, actual_val, absolute_tolerance, relative_tolerance)
    else:
        return expected_val != actual_val


def _two_numbers_are_different(expected_val, actual_val, absolute_tolerance, relative_tolerance):
    if not is_finite_number(actual_val):
        return True
    else:
        return abs(actual_val - expected_val) > absolute_tolerance + relative_tolerance * abs(expected_val)


def assert_series_equal(expected_series: pd.Series, actual_series: pd.Series,
                        check_series_type: bool = True, check_dtype: bool = False, check_index_type: bool = False,
                        check_names: bool = True, absolute_tolerance: float = 1e-4, relative_tolerance: float = 0.0):
    """
    Checks if two series are the same. Values of the series are considered to be the same if:
        abs(actual_series - expected_series) <= absolute_tolerance + relative_tolerance * abs(expected_series)

    Parameters
    ----------
    expected_series
        second series to compare (compared with the first one)
    actual_series
        first series to compare
    check_series_type
        True if the series' types should be the same
    check_dtype
        True if the type of data stored in the series should be the same in both series
    check_index_type
        True if the type of index for series should be the same in both series
    check_names
        True if the names of the series should be the same
    absolute_tolerance
        see the description of the method
    relative_tolerance
        see the description of the method

    Raises
    -------
    ex: AssertionError
        exception thrown when two time series are not almost equal
    """
    assert isinstance(expected_series, pd.Series), "Expected series is not an instance of pandas.Series"
    assert isinstance(actual_series, pd.Series), "Actual series is not an instance of pandas.Series"

    if check_series_type:
        _assert_same_container_type(expected_series, actual_series)

    _assert_same_containers_shape(expected_series, actual_series)

    if check_dtype:
        _assert_same_data_type(expected_series, actual_series)

    assert_same_index(expected_series.index, actual_series.index, check_index_type, check_names)

    if check_names:
        _assert_same_series_names(expected_series, actual_series)

    _assert_same_series_values(expected_series, actual_series, absolute_tolerance, relative_tolerance)


def assert_dataframes_equal(expected_frame: pd.DataFrame, actual_frame: pd.DataFrame,
                            check_frame_type: bool = True, check_dtype: bool = False, check_index_type: bool = False,
                            check_column_type: bool = False, check_names=True, absolute_tolerance: float = 1e-4,
                            relative_tolerance: float = 0.0):
    """
    Checks if two series are the same. Values of the series are considered to be the same if:
        abs(actual_series - expected_series) <= absolute_tolerance + relative_tolerance * abs(expected_series)

    Parameters
    ----------
    expected_frame
        second series to compare (compared with the first one)
    actual_frame
        first series to compare
    check_frame_type
        True if the series' types should be the same
    check_dtype
        True if the type of data stored in the series should be the same in both series
    check_index_type
        True if the type of index for series should be the same in both series
    check_column_type
        True if the names of the series should be the same
    check_names
        True if the names of the columns should be the same
    absolute_tolerance
        see the description of the method
    relative_tolerance
        see the description of the method

    Raises
    -------
    ex: AssertionError
        exception thrown when two time series are not almost equal
    """
    assert isinstance(expected_frame, pd.DataFrame), "Expected frame is not an instance of pandas.DataFrame"
    assert isinstance(actual_frame, pd.DataFrame), "Actual frame is not an instance of pandas.DataFrame"

    if check_frame_type:
        _assert_same_container_type(expected_frame, actual_frame)

    _assert_same_containers_shape(expected_frame, actual_frame)

    if check_dtype:
        _assert_same_data_type(expected_frame, actual_frame)

    assert_same_index(expected_frame.index, actual_frame.index, check_index_type, check_names)
    assert_same_index(expected_frame.columns, actual_frame.columns, check_index_type, check_names)

    if check_column_type:
        _assert_same_column_type(expected_frame, actual_frame)

    for i in range(len(expected_frame.columns)):
        expected_column = expected_frame.iloc[:, i]
        actual_column = actual_frame.iloc[:, i]

        _assert_same_series_values(expected_column, actual_column, absolute_tolerance, relative_tolerance)


def _assert_same_container_type(expected_container, actual_container):
    expected_type = type(expected_container)
    actual_type = type(actual_container)
    if actual_type != expected_type:
        raise AssertionError("Container has an incorrect type. Expected: {:s}, actual: {:s}"
                             .format(str(expected_type), str(actual_type)))


def _assert_same_containers_shape(expected_container, actual_container):
    expected_shape = expected_container.shape
    actual_shape = actual_container.shape
    if actual_shape != expected_shape:
        raise AssertionError("Container has incorrect shape. Expected: {:s}, actual: {:s}"
                             .format(str(expected_shape), str(actual_shape)))


def _assert_same_data_type(expected_container, actual_container):
    if actual_container.dtype != expected_container.dtype:
        raise AssertionError("Container has an incorrect data type. Expected: {:s}, actual: {:s}"
                             .format(str(expected_container.dtype), str(actual_container.dtype)))


def assert_same_index(expected_index, actual_index, check_index_type, check_names):
    if check_index_type:
        _assert_same_index_type(expected_index, actual_index)

    if check_names:
        expected_index_name = expected_index.name
        actual_index_name = actual_index.name
        if expected_index_name != actual_index_name:
            raise AssertionError("Incorrect index name. Expected {:s}, actual: {:s}".format(
                str(expected_index_name), str(actual_index_name)))

    assert_same_axis_values(expected_index, actual_index)


def assert_same_axis_values(expected_index, actual_index):
    different_index_values = expected_index.values != actual_index.values
    if np.any(different_index_values):
        diffrent_values_pos = np.where(different_index_values)[0]
        messages = ["Different axis values on positions: {:s}".format(str(diffrent_values_pos))]

        for diff_position in diffrent_values_pos:
            msg = "{:d}: Expected: {:s}   Actual: {:s}".format(
                diff_position, str(expected_index[diff_position]), str(actual_index[diff_position])
            )
            messages.append(msg)

        raise AssertionError("\n".join(messages))


def _assert_same_index_type(expected_index, actual_index):
    expected_index_type = type(expected_index)
    actual_index_type = type(actual_index)
    if actual_index_type != expected_index_type:
        raise AssertionError("Container has an incorrect index type. Expected: {:s}, actual: {:s}"
                             .format(str(expected_index_type), str(actual_index_type)))


def _assert_same_column_type(expected_frame, actual_frame):
    expected_type = type(expected_frame.columns)
    actual_type = type(actual_frame.columns)
    if actual_type != expected_type:
        raise AssertionError("Container has an incorrect column type. Expected: {:s}, actual: {:s}"
                             .format(str(expected_type), str(actual_type)))


def _assert_same_series_names(expected_series, actual_series):
    if actual_series.name != expected_series.name:
        raise AssertionError("Series has incorrect name. Expected: {:s}, actual: {:s}"
                             .format(expected_series.name, actual_series.name))


def _assert_same_series_values(expected_series, actual_series, absolute_tolerance, relative_tolerance):
    expected_values = expected_series.values.astype('float64')
    actual_values = actual_series.values.astype('float64')

    same_values_idx = np.isclose(actual_values, expected_values, rtol=relative_tolerance, atol=absolute_tolerance)

    # np.nan != np.nan thus it is necessary to remove indices corresponding to expected nans
    # from the different_values_idx array
    expected_nans_idx = np.isnan(expected_values)
    actual_nans_idx = np.isnan(actual_values)
    both_nans_idx = np.logical_and(expected_nans_idx, actual_nans_idx)
    different_values_idx = np.logical_and(np.logical_not(same_values_idx), np.logical_not(both_nans_idx))

    if np.any(different_values_idx):
        index_labels_for_incorrect_vals = actual_series.index.values[different_values_idx]
        expected_vals = expected_series[different_values_idx]
        actual_vals = actual_series[different_values_idx]

        messages = []

        for label, expected_val, actual_val in zip(index_labels_for_incorrect_vals, expected_vals, actual_vals):
            messages.append("{:s} - Expected: {:f}, actual: {:f}".format(str(label), expected_val, actual_val))

        raise AssertionError("Different series values for labels:\n" + "\n".join(messages))
