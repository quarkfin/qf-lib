from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries


def squeeze_panel(original_data_panel, got_single_date, got_single_ticker, got_single_field):
    original_shape = original_data_panel.shape

    # slice(None) corresponds to ':' in iloc[:] notation
    dates_indices = 0 if got_single_date else slice(None)
    tickers_indices = 0 if got_single_ticker else slice(None)
    fields_indices = 0 if got_single_field else slice(None)

    container = original_data_panel.iloc[dates_indices, tickers_indices, fields_indices]

    # correction of containers axis order (if last or pre-last axis is being removed, than the data frame needs
    # to be transposed to keep the axis order: dates, tickers, fields)
    if len(container.shape) == 2 and (original_shape[1] == 1 or original_shape[2] == 1):
        container = container.transpose()

    # if single ticker was provided, name the series or data frame by the ticker
    if original_shape[1] == 1 and original_shape[2] == 1:
        container.name = original_data_panel.major_axis[0].as_string()

    return container


def cast_result_to_proper_type(result):
    num_of_dimensions = len(result.axes)
    if num_of_dimensions == 1:
        casted_result = cast_series(result, QFSeries)
    elif num_of_dimensions == 2:
        casted_result = cast_dataframe(result, QFDataFrame)
    else:
        casted_result = result

    return casted_result
