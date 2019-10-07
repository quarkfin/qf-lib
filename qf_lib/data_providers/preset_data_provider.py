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

from datetime import datetime
from typing import Union, Sequence, Set, Type
import numpy as np
import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import DATES
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.data_providers.price_data_provider import DataProvider


class PresetDataProvider(DataProvider):
    """
    Wrapper on QFDataArray which makes it a DataProvider.
    """

    def __init__(
            self, data: QFDataArray, start_date: datetime, end_date: datetime, frequency: Frequency, check_data_availability: bool = True):
        """
        Parameters
        ----------
        data
            data to be wrapped
        start_date
            beginning of the cached period (not necessarily the first date in the `data`)
        end_date
            end of the cached period (not necessarily the last date in the `data`)
        frequency
            frequency of the data
        check_data_availability
            True by default. If False then if there's a call for a non-existent piece of data, some strange behaviour
            may occur (e.g. nans returned).
        """
        self._data_bundle = data
        self._check_data_availability = check_data_availability
        self.frequency = frequency

        if self._check_data_availability:
            self._tickers_cached_set = set(data.tickers.values)
            self._fields_cached_set = set(data.fields.values)
            self._start_date = start_date
            self._end_date = end_date

        self._ticker_types = {type(ticker) for ticker in data.tickers.values}

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY) ->\
            Union[None, PricesSeries, PricesDataFrame, QFDataArray]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, PriceField)

        got_single_date = False if frequency > Frequency.DAILY else (
            bool(start_date and (start_date == end_date))
        )

        if self._check_data_availability:
            self._check_if_cached_data_available(tickers, fields, start_date, end_date)

        if frequency > Frequency.DAILY:
            # In case of high frequency - the data array should not include the end_date. The data range is
            # labeled with the beginning index time and excludes the end of the time range, therefore a new
            # end date is computed.
            end_date = end_date - Frequency.MIN_1.time_delta()

        data_array = self._data_bundle.loc[start_date:end_date, tickers, fields]

        # The passed desired data frequency should be at most equal to the frequency of the initially loaded data
        # (in case of downsampling the data may be aggregated, but no data upsampling is supported).
        assert frequency <= self.frequency

        # The data should be aggregated - allowed only for the Intraday Data
        if frequency < self.frequency and len(data_array[DATES]) > 0:

            if frequency <= Frequency.DAILY:
                raise NotImplementedError("Data aggregation for lower than daily frequency is not supported yet")

            # If the data is of intraday data type, which spans over multiple days, the base parameter of resamples
            # function should be adjusted differently for the first day. Therefore, the data array is divided into two
            # separate arrays - first containing only the first day, and the second one - containing all other dates.
            end_of_day = start_date + RelativeDelta(hour=23, minute=59, second=59)
            _end_date = end_of_day if (end_of_day < end_date) else end_date

            data_array_1 = data_array.loc[start_date:_end_date, :, :]

            if len(data_array_1) > 0:

                base_data_array_1 = pd.to_datetime(data_array_1[DATES].values[0]).minute

                data_array_1 = data_array_1.resample(
                    dates=frequency.to_pandas_freq(),
                    base=base_data_array_1,
                    label='left',
                    skipna=True
                ).apply(
                    lambda x: self._aggregate_data_array(x, tickers, fields)
                )

            # Get the second part of the data array
            data_array_2 = data_array.loc[end_of_day:end_date, :, :]

            if len(data_array_2) > 0:
                base_data_array_2 = pd.to_datetime(data_array_2[DATES].values[0]).minute

                data_array_2 = data_array_2.resample(
                    dates=frequency.to_pandas_freq(),
                    base=base_data_array_2,
                    label='left',
                    skipna=True
                ).apply(
                    lambda x: self._aggregate_data_array(x, tickers, fields)
                )

            data_array = QFDataArray.concat([data_array_1, data_array_2], dim=DATES)

        normalized_result = normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=True)
        return normalized_result

    def _check_if_cached_data_available(self, tickers, fields, start_date, end_date):
        # tickers which are not cached but were requested
        uncached_tickers = set(tickers) - self._tickers_cached_set
        if uncached_tickers:
            raise ValueError("Tickers: {} are not available in the Data Bundle".format(tickers))

        # fields which are not cached but were requested
        uncached_fields = set(fields) - self._fields_cached_set
        if uncached_fields:
            raise ValueError("Fields: {} are not available in the Data Bundle".format(fields))

        if start_date < self._start_date:
            raise ValueError("Requested start date {} is before data bundle start date {}".
                             format(start_date, self._start_date))
        if end_date > self._end_date:
            raise ValueError("Requested end date {} is after data bundle end date {}".
                             format(end_date, self._end_date))

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]],
                    fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY, **kwargs
                    ) -> Union[QFSeries, QFDataFrame, QFDataArray]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, str)
        got_single_date = start_date is not None and (
            (start_date == end_date) if frequency <= Frequency.DAILY else
            (start_date + frequency.time_delta() >= end_date)
        )

        if self._check_data_availability:
            self._check_if_cached_data_available(tickers, fields, start_date, end_date)

        if frequency > Frequency.DAILY:
            # In case of high frequency - the data array should not include the end_date. The data range is
            # labeled with the beginning index time and excludes the end of the time range, therefore a new
            # end date is computed.
            end_date = end_date - Frequency.MIN_1.time_delta()

        data_array = self._data_bundle.loc[start_date:end_date, tickers, fields]

        # Currently, for the get history does not support data sampling
        assert frequency == self.frequency

        normalized_result = normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker,
                                                 got_single_field, use_prices_types=False)

        return normalized_result

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return self._ticker_types

    @staticmethod
    def _aggregate_data_array(data_array, tickers: Sequence[Ticker], fields: Sequence[PriceField]):
        """
        Function, which aggregates the data arrays for various dates and returns a data array consisting of
        tickers and fields.
        """

        returned_frame = data_array[0]

        price_field_to_data = {
            PriceField.High: data_array.loc[:, :].max(dim=DATES),
            PriceField.Low: data_array.loc[:, :].min(dim=DATES),
            PriceField.Volume: data_array.loc[:, :].sum(dim=DATES),
        }

        for field in fields:
            if field in price_field_to_data.keys():
                returned_frame.loc[:, field] = price_field_to_data[field].loc[:, field]
            elif field in (PriceField.Open, PriceField.Close):
                # Get the first / last bar field value, which is not a Nan
                date_index = {
                    PriceField.Open: 0,   # Look for the first date with non-Nan field value
                    PriceField.Close: -1  # Look for the last date with non-Nan field value
                }

                for ticker in tickers:
                    not_nan_fields = np.where(~np.isnan(data_array.loc[:, ticker, field]))[0]
                    if len(not_nan_fields) > 0:
                        index = not_nan_fields[date_index[field]]
                        returned_frame.loc[ticker, field] = data_array[index].loc[ticker, field]
                    else:
                        # This ticker does not contain any value different than Nan for this field
                        returned_frame.loc[ticker, field] = np.nan

        return returned_frame
