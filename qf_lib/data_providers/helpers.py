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

from typing import Union, Dict

import pandas as pd

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS, FIELDS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


def normalize_data_array(
        data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=False) \
        -> Union[QFSeries, QFDataFrame, QFDataArray, PricesSeries, PricesDataFrame]:
    """
    Post-processes the result of some DataProviders so that it satisfies the format of a result expected
    from DataProviders:
    - proper return type (QFSeries/PricesSeries, QFDataFrame/PricesDataFrame, QFDataArray),
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
        if True then proper return types are: PricesSeries, PricesDataFrame or QFDataArray;
        otherwise return types are: QFSeries, QFDataFrame or QFDataArray
    """
    # to keep the order of tickers and fields we reindex the data_array
    data_array = data_array.reindex(tickers=tickers, fields=fields)

    squeezed_result = squeeze_data_array(data_array, got_single_date, got_single_ticker, got_single_field)
    casted_result = cast_data_array_to_proper_type(squeezed_result, use_prices_types)

    return casted_result


def squeeze_data_array(original_data_array, got_single_date, got_single_ticker, got_single_field):
    original_shape = original_data_array.shape

    dimensions_to_squeeze = []
    if got_single_date:
        dimensions_to_squeeze.append(DATES)
    if got_single_ticker:
        dimensions_to_squeeze.append(TICKERS)
    if got_single_field:
        dimensions_to_squeeze.append(FIELDS)

    if dimensions_to_squeeze:
        container = original_data_array.squeeze(dimensions_to_squeeze)
    else:
        container = original_data_array

    # if single ticker was provided, name the series or data frame by the ticker
    if original_shape[1] == 1 and original_shape[2] == 1:
        ticker = original_data_array.tickers[0].item()
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


def cast_dataframe_to_proper_type(result):
    num_of_dimensions = len(result.axes)
    if num_of_dimensions == 1:
        casted_result = cast_series(result, QFSeries)
    elif num_of_dimensions == 2:
        casted_result = cast_dataframe(result, QFDataFrame)
    else:
        casted_result = result

    return casted_result


def tickers_dict_to_data_array(tickers_data_dict: Dict[Ticker, pd.DataFrame], requested_tickers, requested_fields) -> QFDataArray:
    """
    Converts a dictionary tickers->DateFrame to QFDataArray.

    Parameters
    ----------
    tickers_data_dict
        Ticker -> DataFrame[dates, fields]
    requested_tickers
    requested_fields

    Returns
    -------
    QFDataArray
    """
    # return empty xr.DataArray if there is no data to be converted
    if not tickers_data_dict:
        return QFDataArray.create(dates=[], tickers=requested_tickers, fields=requested_fields)

    tickers = []
    data_arrays = []
    for ticker, df in tickers_data_dict.items():
        df.index.name = DATES
        if df.empty:  # if there is no data for a given ticker, skip it (proper column will be added afterwards anyway)
            continue

        data_array = df.to_xarray()
        data_array = data_array.to_array(dim=FIELDS, name=ticker)
        data_array = data_array.transpose(DATES, FIELDS)

        tickers.append(ticker)
        data_arrays.append(data_array)

    tickers_index = pd.Index(tickers, name=TICKERS)
    if not data_arrays:
        return QFDataArray.create(dates=[], tickers=requested_tickers, fields=requested_fields)
    result = QFDataArray.concat(data_arrays, dim=tickers_index)

    # the DataArray gets a name after the first ticker in the tickers_data_dict.keys() which is incorrect;
    # it should have no name
    result.name = None

    return result


def get_fields_from_tickers_data_dict(tickers_data_dict):
    fields = set()
    for dates_fields_df in tickers_data_dict.values():
        fields.update(dates_fields_df.columns.values)

    fields = list(fields)
    return fields
