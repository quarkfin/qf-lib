from typing import Union

import numpy as np
import pandas as pd
from xarray import DataArray

from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


def squeeze_panel(original_data_panel, got_single_date, got_single_ticker, got_single_field):
    original_shape = original_data_panel.shape

    # slice(None) corresponds to ':' in iloc[:] notation
    dates_indices = 0 if got_single_date else slice(None)
    tickers_indices = 0 if got_single_ticker else slice(None)
    fields_indices = 0 if got_single_field else slice(None)

    container = original_data_panel.iloc[dates_indices, tickers_indices, fields_indices]

    # correction of containers axis order (if last or penultimate axis is being removed, than the data frame needs
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


def normalize_data_array(
    data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=False
) -> Union[QFSeries, QFDataFrame, pd.Panel, PricesSeries, PricesDataFrame]:
    """
    Post-processes the result of some DataProviders so that it satisfies the format of a result expected
    from DataProviders:
    - proper return type (QFSeries, QFDataFrame or pandas.Panel) or (PricesSeries, PricesDataFrame or pandas.Panel),
    - proper shape of the result (squeezed dimensions for which a single non-list value was provided, e.g. "OPEN"),
    - dimensions: "tickers" and "fields" contain all required labels and the labels are in required order.

    Parameters
    ----------
    data_array
        data_array to be normalized
    tickers
        list of tickers requested by the caller
    fields
        list of fields requested by the caller
    got_single_date
        True if a single (scalar value) date was requested (start_date==end_date); False otherwise
    got_single_ticker
        True if a single (scalar value) ticker was requested (e.g. "MSFT US Equity"); False otherwise
    got_single_field
        True if a single (scalar value) field was requested (e.g. "OPEN"); False otherwise
    use_prices_types
        if True then proper return types are: PricesSeries, PricesDataFrame or pandas.Panel;
        otherwise return types are: QFSeries, QFDataFrame or pandas.Panel
    """
    # to keep the order of tickers and fields we reindex the data_array
    data_array = data_array.reindex(tickers=tickers, fields=fields)
    data_array = data_array.sortby(QFDataArray.DATES)

    squeezed_result = squeeze_data_array(data_array, got_single_date, got_single_ticker, got_single_field)
    casted_result = cast_data_array_to_proper_type(squeezed_result, use_prices_types)

    # remove this conversion after switching to xarray.DataArray from pd.Panels everywhere
    if isinstance(casted_result, QFDataArray):
        casted_result = casted_result.to_pandas()

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


def cast_data_array_to_proper_type(result: QFDataArray, use_prices_types=False):
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


def tickers_dict_to_data_array(tickers_data_dict, requested_tickers, requested_fields) -> QFDataArray:
    """
    Converts a dictionary tickers->DateFrame to QFDataArray.

    Parameters
    ----------
    tickers_data_dict: ticker -> DataFrame[dates, fields]
    requested_tickers
    requested_fields

    Returns
    -------
    DataArray  [date, ticker, field]
    """
    # return empty xr.DataArray if there is no data to be converted
    if not tickers_data_dict:
        data = np.empty((0, len(requested_tickers), len(requested_fields)))
        return QFDataArray.create(data, dates=[], tickers=requested_tickers, fields=requested_fields)

    tickers = []
    data_arrays = []
    for ticker, df in tickers_data_dict.items():
        df.index.name = QFDataArray.DATES
        data_array = df.to_xarray()
        data_array = data_array.to_array(dim=QFDataArray.FIELDS, name=ticker)
        data_array = data_array.transpose(QFDataArray.DATES, QFDataArray.FIELDS)

        tickers.append(ticker)
        data_arrays.append(data_array)

    tickers_index = pd.Index(tickers, name=QFDataArray.TICKERS)
    result = QFDataArray.concat(data_arrays, dim=tickers_index)

    return result


def get_fields_from_tickers_to_data_dict(tickers_data_dict):
    fields = set()
    for dates_fields_df in tickers_data_dict.values():
        fields.update(dates_fields_df.columns.values)

    fields = list(fields)
    return fields
