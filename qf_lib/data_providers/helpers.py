from xarray import DataArray

from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


def squeeze_panel(original_data_panel, got_single_date, got_single_ticker, got_single_field):
    original_shape = original_data_panel.shape

    # slice(None) corresponds to ':' in iloc[:] notation
    dates_indices = 0 if got_single_date else slice(None)
    tickers_indices = 0 if got_single_ticker else slice(None)
    fields_indices = 0 if got_single_field else slice(None)

    container = original_data_panel[dates_indices, tickers_indices, fields_indices]

    # correction of containers axis order (if last or penultimate axis is being removed, than the data frame needs
    # to be transposed to keep the axis order: dates, tickers, fields)
    if len(container.shape) == 2 and (original_shape[1] == 1 or original_shape[2] == 1):
        container = container.transpose()

    # if single ticker was provided, name the series or data frame by the ticker
    if original_shape[1] == 1 and original_shape[2] == 1:
        ticker = original_data_panel.major_axis[0].item()
        container.name = ticker.as_string()

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


def squeeze_data_array(original_data_panel, got_single_date, got_single_ticker, got_single_field):
    original_shape = original_data_panel.shape

    # slice(None) corresponds to ':' in iloc[:] notation
    dates_indices = 0 if got_single_date else slice(None)
    tickers_indices = 0 if got_single_ticker else slice(None)
    fields_indices = 0 if got_single_field else slice(None)

    container = original_data_panel[dates_indices, tickers_indices, fields_indices]

    # if single ticker was provided, name the series or data frame by the ticker
    if original_shape[1] == 1 and original_shape[2] == 1:
        ticker = original_data_panel.tickers[0].item()
        container.name = ticker.as_string()

    return container


def cast_data_array_to_proper_type(result: DataArray, use_prices_types=False):
    if use_prices_types:
        series_type = PricesSeries
        data_frame_type = PricesDataFrame
    else:
        series_type = QFSeries
        data_frame_type = QFDataFrame

    num_of_dimensions = len(result.shape)
    if num_of_dimensions == 0:
        casted_result = result.item()
    elif num_of_dimensions == 1:
        casted_result = cast_series(result.to_pandas(), series_type)
        casted_result.name = result.name
    elif num_of_dimensions == 2:
        casted_result = cast_dataframe(result.to_pandas(), data_frame_type)
    else:
        casted_result = result

    return casted_result
