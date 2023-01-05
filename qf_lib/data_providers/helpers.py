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
import warnings
from datetime import datetime
from typing import Union, Dict, Sequence, Any
import pandas as pd
from pandas import DatetimeIndex
from xarray import DataArray

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS, FIELDS
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


def normalize_data_array(
        data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=False) \
        -> Union[QFSeries, QFDataFrame, QFDataArray, PricesSeries, PricesDataFrame]:
    """
    Post-processes the result of some DataProviders so that it satisfies the format of a result expected
    from DataProviders. Expected format rules should cover the following:
    - proper return type (QFSeries/PricesSeries, QFDataFrame/PricesDataFrame, QFDataArray),
    - proper shape of the result (squeezed dimensions for which a single non-list value was provided, e.g. "OPEN"),
    - dimensions: TICKERS and FIELDS contain all required labels and the labels are in required order.

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

    Returns
    --------
    QFSeries, QFDataFrame, QFDataArray, PricesSeries, PricesDataFrame
    """
    # to keep the order of tickers and fields we reindex the data_array
    if data_array.tickers.values.tolist() != tickers:
        data_array = data_array.reindex(tickers=tickers)
    if data_array.fields.values.tolist() != fields:
        data_array = data_array.reindex(fields=fields)

    data_array = data_array.dropna(DATES, how='all')
    squeezed_and_casted_result = squeeze_data_array_and_cast_to_proper_type(data_array, got_single_date,
                                                                            got_single_ticker,
                                                                            got_single_field,
                                                                            use_prices_types)

    return squeezed_and_casted_result


def squeeze_data_array_and_cast_to_proper_type(original_data_array: QFDataArray, got_single_date: bool,
                                               got_single_ticker: bool, got_single_field: bool, use_prices_types: bool):

    if isinstance(original_data_array, DataArray) and not isinstance(original_data_array, QFDataArray):
        warnings.warn("data_array to be normalized should be a QFDataFrame instance. "
                      "Transforming data_array to QFDataArray. Please check types in the future.")
        original_data_array = QFDataArray.from_xr_data_array(original_data_array)

    dimensions_to_squeeze = []
    if got_single_date:
        dimensions_to_squeeze.append(DATES)
    if got_single_ticker:
        dimensions_to_squeeze.append(TICKERS)
    if got_single_field:
        dimensions_to_squeeze.append(FIELDS)

    container = original_data_array
    if dimensions_to_squeeze:
        if original_data_array.size == 0:  # empty
            container = QFDataFrame(index=original_data_array[TICKERS].values,
                                    columns=original_data_array[FIELDS].values)
            container.index.name = TICKERS
            container.columns.name = FIELDS

            if use_prices_types:
                container = PricesDataFrame(container)
            if got_single_field:
                container = container.squeeze(axis=1)
                container.name = original_data_array[FIELDS].values[0]
            if got_single_ticker:
                container = container.squeeze(axis=0)
            if not got_single_date:
                dates = DatetimeIndex([], name=DATES)
                if got_single_ticker and got_single_field:
                    container = QFSeries(index=DatetimeIndex([], name=DATES))
                if use_prices_types:
                    container = PricesSeries(container)
                if not got_single_ticker or not got_single_field:
                    container = container.to_frame().T.reindex(dates)
                    container.index.name = DATES
        else:
            container = original_data_array.squeeze(dimensions_to_squeeze)

    if len(dimensions_to_squeeze) < 3:
        if got_single_ticker:
            ticker = original_data_array.tickers[0].item()
            container.name = ticker.as_string()
        elif got_single_field:
            container.name = original_data_array.fields[0].item()

    if isinstance(container, QFDataArray):
        container = cast_data_array_to_proper_type(container, use_prices_types)

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


def tickers_dict_to_data_array(tickers_data_dict: Dict[Ticker, QFDataFrame],
                               requested_tickers: Union[Ticker, Sequence[Ticker]],
                               requested_fields: Union[Any, Sequence[Any]]) -> QFDataArray:
    """
    Converts a dictionary mapping tickers to DateFrame onto a QFDataArray,
    by applying a filter on the tickers and fields that are needed

    Parameters
    ----------
    tickers_data_dict:  Dict[Ticker, QFDataFrame]
        Ticker -> QFDataFrame[dates, fields]
    requested_tickers: Sequence[Ticker]
        Filter the data dict based on a list of tickers
    requested_fields
        Filter the data dict based on a list of fields
    Returns
    -------
    QFDataArray
    """
    # return empty xr.DataArray if there is no data to be converted
    requested_tickers, _ = convert_to_list(requested_tickers, Ticker)
    if not isinstance(requested_fields, Sequence) or isinstance(requested_fields, str):
        requested_fields, _ = convert_to_list(requested_fields, type(requested_fields))

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

    if not data_arrays:
        return QFDataArray.create(dates=[], tickers=requested_tickers, fields=requested_fields)

    tickers_index = pd.Index(tickers, name=TICKERS)
    result = QFDataArray.concat(data_arrays, dim=tickers_index)
    result = result.reindex(tickers=requested_tickers, fields=requested_fields)

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


def chain_tickers_within_range(future_ticker: FutureTicker, exp_dates: QFDataFrame, start_date: datetime,
                               end_date: datetime):
    """
    Returns only these tickers belonging to the chain of a given FutureTicker, which were valid only for the given
    time frame.

    As it is possible to select the contracts to be traded for a given future ticker (e.g. for Bloomberg
    future tickers we could specify only to trade "M" contracts), the end date is computed as the original end date
    + 1 year x contract number to trade.
    E.g. if we specify that we only want to trade "M" contracts and we always want to trade the front M contract,
    we add 1 year x 1. If instead of the front M, we would like to trade the second next M contract,
    we add 2 years to the end date etc.
    """
    exp_dates = exp_dates[exp_dates >= start_date].dropna()
    exp_dates = exp_dates[exp_dates <= end_date + RelativeDelta(years=future_ticker.N)].dropna()
    return exp_dates.index.tolist()
