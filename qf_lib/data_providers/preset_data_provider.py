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
from typing import Union, Sequence, Any, Set, Type, Dict, FrozenSet, Optional, Tuple

import pandas as pd
from numpy import nan

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import DATES, FIELDS, TICKERS
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array


class PresetDataProvider(DataProvider):
    """
    Wrapper on QFDataArray which makes it a DataProvider.

    Parameters
    ----------
    data
        data to be wrapped, indexed by date, (specific) tickers and fields
    start_date
        beginning of the cached period (not necessarily the first date in the `data`)
    end_date
        end of the cached period (not necessarily the last date in the `data`)
    frequency
        frequency of the data
    exp_dates
        dictionary mapping FutureTickers to QFDataFrame of contracts expiration dates, belonging to the certain
        future ticker family
    """

    def __init__(self, data: QFDataArray, start_date: datetime, end_date: datetime, frequency: Frequency,
                 exp_dates: Dict[FutureTicker, QFDataFrame] = None):
        super().__init__()
        self._data_bundle = data
        self._frequency = frequency
        self._exp_dates = exp_dates

        self._tickers_cached_set = frozenset(data.tickers.values)
        self._future_tickers_cached_set = frozenset(exp_dates.keys()) if exp_dates is not None else None
        self._fields_cached_set = frozenset(data.fields.values)
        self._start_date = start_date
        self._end_date = end_date

        self._ticker_types = {type(ticker) for ticker in data.tickers.values}

    @property
    def data_bundle(self) -> QFDataArray:
        return self._data_bundle

    @property
    def frequency(self) -> Frequency:
        return self._frequency

    @property
    def exp_dates(self) -> Dict[FutureTicker, QFDataFrame]:
        return self._exp_dates

    @property
    def cached_tickers(self) -> FrozenSet[Ticker]:
        return self._tickers_cached_set

    @property
    def cached_future_tickers(self) -> FrozenSet[FutureTicker]:
        return self._future_tickers_cached_set

    @property
    def cached_fields(self) -> FrozenSet[Union[str, PriceField]]:
        return self._fields_cached_set

    @property
    def start_date(self) -> datetime:
        return self._start_date

    @property
    def end_date(self) -> datetime:
        return self._end_date

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return self._ticker_types

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY) -> \
            Union[None, PricesSeries, PricesDataFrame, QFDataArray]:
        # The passed desired data frequency should be at most equal to the frequency of the initially loaded data
        # (in case of downsampling the data may be aggregated, but no data upsampling is supported).
        assert frequency <= self._frequency, "The passed data frequency should be at most equal to the frequency of " \
                                             "the initially loaded data"
        # The PresetDataProvider does not support data aggregation for frequency lower than daily frequency
        if frequency < self._frequency and frequency <= Frequency.DAILY:
            self.logger.warning("aggregating intraday data to frequency Daily or lower is based on the time of "
                                "underlying intrady data and might not be identical to getting daily data form the "
                                "data provider.")

        start_date = self._adjust_start_date(start_date, frequency)
        end_date = self._adjust_end_date(end_date)

        tickers, specific_tickers, tickers_mapping, got_single_ticker = self._tickers_mapping(tickers)
        fields, got_single_field = convert_to_list(fields, PriceField)
        got_single_date = self._got_single_date(start_date, end_date, frequency)

        self._check_if_cached_data_available(specific_tickers, fields, start_date, end_date)
        data_array = self._data_bundle.loc[start_date:end_date, specific_tickers, fields]

        # Data aggregation
        if frequency < self._frequency and data_array.shape[0] > 0:
            data_array = self._aggregate_bars(data_array, fields, frequency)

        normalized_result = normalize_data_array(
            data_array, specific_tickers, fields, got_single_date, got_single_ticker, got_single_field,
            use_prices_types=True
        )

        normalized_result = self._map_normalized_result(normalized_result, tickers_mapping, tickers)

        return normalized_result

    def historical_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                         fields: Union[PriceField, Sequence[PriceField]],
                         nr_of_bars: int, end_date: Optional[datetime] = None,
                         frequency: Frequency = None) -> Union[PricesSeries, PricesDataFrame, QFDataArray]:

        assert nr_of_bars > 0, "Numbers of data samples should be a positive integer"
        end_date = datetime.now() if end_date is None else end_date

        tickers, specific_tickers, tickers_mapping, got_single_ticker = self._tickers_mapping(tickers)
        fields, got_single_field = convert_to_list(fields, PriceField)
        got_single_date = nr_of_bars == 1

        start_date = self._compute_start_date(nr_of_bars, end_date, frequency)
        data_bundle = self._data_bundle.loc[start_date:end_date, specific_tickers, fields].dropna(DATES, how='all')

        if frequency < self._frequency and data_bundle.shape[0] > 0:  # Aggregate bars to desired frequency
            data_bundle = self._aggregate_bars(data_bundle, fields, frequency)

        self._check_data_availibility(data_bundle, end_date, nr_of_bars, tickers)
        data_bundle = data_bundle.isel(dates=slice(-nr_of_bars, None))

        normalized_result = normalize_data_array(
            data_bundle, specific_tickers, fields, got_single_date, got_single_ticker, got_single_field,
            use_prices_types=True)

        normalized_result = self._map_normalized_result(normalized_result, tickers_mapping, tickers)
        self._check_data_availibility(normalized_result, end_date, nr_of_bars, tickers)
        return normalized_result

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency,
                                 end_time: Optional[datetime] = None) -> Union[float, PricesSeries]:
        end_time = datetime.now() if end_time is None else end_time
        end_time += RelativeDelta(second=0, microsecond=0)

        assert frequency >= Frequency.DAILY, "Frequency lower then daily is not supported by the " \
                                             "get_last_available_price function"

        tickers, specific_tickers, tickers_mapping, got_single_ticker = self._tickers_mapping(tickers)

        if not tickers:
            return nan if got_single_ticker else PricesSeries()

        start_time = end_time - RelativeDelta(days=7)  # 7 days to know if an asset disappears
        data_array = self._data_bundle.loc[start_time:end_time, specific_tickers, [PriceField.Open, PriceField.Close]]

        # Get the Close price of latest bar if available for all the tickers
        last_close = data_array.isel(dates=slice(-1, None)).loc[:, :, [PriceField.Close]]
        if not last_close.isnull().any():
            normalized_result = normalize_data_array(last_close, specific_tickers, [PriceField.Close],
                                                     got_single_date=True, got_single_ticker=got_single_ticker,
                                                     got_single_field=True, use_prices_types=True)
            normalized_result = self._map_normalized_result(normalized_result, tickers_mapping, tickers)
            return normalized_result

        open_prices = data_array.loc[:, :, [PriceField.Open]].squeeze(axis=2).to_pandas()
        close_prices = data_array.loc[:, :, [PriceField.Close]].squeeze(axis=2).to_pandas()

        first_indices = [df.first_valid_index().to_pydatetime() for df in [open_prices, close_prices] if
                         df.first_valid_index() is not None]
        if not first_indices:
            return nan if got_single_ticker else PricesSeries(index=tickers)

        start_date = min(first_indices)
        latest_available_prices_series = self._get_valid_latest_available_prices(start_date, specific_tickers,
                                                                                 open_prices, close_prices)

        latest_available_prices_series = self._map_normalized_result(latest_available_prices_series, tickers_mapping, tickers)
        return latest_available_prices_series.iloc[0] if got_single_ticker else latest_available_prices_series

    def _tickers_mapping(self, tickers: Union[Ticker, Sequence[Ticker]]) -> \
            Tuple[Sequence[Ticker], Sequence[Ticker], Dict, bool]:
        """ In order to be able to return data for FutureTickers create a mapping between tickers and corresponding
        specific tickers (in case of non FutureTickers it will be an identity mapping) """
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        tickers_mapping = {(t.get_current_specific_ticker() if isinstance(t, FutureTicker) else t): t for t in tickers}
        specific_tickers = list(tickers_mapping.keys())
        return tickers, specific_tickers, tickers_mapping, got_single_ticker

    def _check_if_cached_data_available(self, tickers, fields, start_date, end_date):
        uncached_tickers = set(tickers) - self._tickers_cached_set
        if uncached_tickers:
            tickers_str = [t.as_string() for t in uncached_tickers]
            raise ValueError("Tickers: {} are not available in the Data Bundle".format(tickers_str))

        # fields which are not cached but were requested
        uncached_fields = set(fields) - self._fields_cached_set
        if uncached_fields:
            raise ValueError("Fields: {} are not available in the Data Bundle".format(uncached_fields))

        def remove_time_part(date: datetime):
            return datetime(date.year, date.month, date.day)

        start_date_not_included = start_date < self._start_date if self._frequency > Frequency.DAILY else \
            remove_time_part(start_date) < remove_time_part(self._start_date)
        if start_date_not_included:
            raise ValueError("Requested start date {} is before data bundle start date {}".
                             format(start_date, self._start_date))

        end_date_not_included = end_date > self._end_date if self._frequency > Frequency.DAILY else \
            remove_time_part(end_date) > remove_time_part(self._end_date)
        if end_date_not_included:
            raise ValueError("Requested end date {} is after data bundle end date {}".
                             format(end_date, self._end_date))

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]],
                    fields: Union[Any, Sequence[Any]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY, **kwargs
                    ) -> Union[QFSeries, QFDataFrame, QFDataArray]:

        # Verify whether the passed frequency parameter is correct and can be used with the preset data
        assert frequency == self._frequency, "Currently, for the get history does not support data sampling"

        start_date = self._adjust_start_date(start_date, frequency)
        end_date = self._adjust_end_date(end_date)

        # In order to be able to return data for FutureTickers create a mapping between tickers and corresponding
        # specific tickers (in case of non FutureTickers it will be an identity mapping)
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        tickers_mapping = {
            (t.get_current_specific_ticker() if isinstance(t, FutureTicker) else t): t for t in tickers
        }
        specific_tickers = list(tickers_mapping.keys())

        fields_type = {type(field) for field in fields} if isinstance(fields, Sequence) else {type(fields)}
        fields, got_single_field = convert_to_list(fields, tuple(fields_type))
        got_single_date = self._got_single_date(start_date, end_date, frequency)

        self._check_if_cached_data_available(specific_tickers, fields, start_date, end_date)
        data_array = self._data_bundle.loc[start_date:end_date, specific_tickers, fields]

        normalized_result = normalize_data_array(data_array, specific_tickers, fields, got_single_date,
                                                 got_single_ticker,
                                                 got_single_field, use_prices_types=False)

        normalized_result = self._map_normalized_result(normalized_result, tickers_mapping, tickers)
        return normalized_result

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, Union[QFSeries, QFDataFrame]]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)

        # Check if the futures tickers are in the exp_dates keys
        uncached_future_tickers = set(tickers) - set(self._exp_dates.keys())
        if uncached_future_tickers:
            tickers_str = [t.name for t in tickers]
            raise ValueError("Tickers: {} are not available in the Data Bundle".format(tickers_str))

        future_chain_tickers = {
            ticker: self._exp_dates[ticker] for ticker in tickers
        }

        return future_chain_tickers

    def _map_normalized_result(self, normalized_result, tickers_mapping, tickers):
        # Map the specific tickers onto the tickers given by the tickers_mapping array
        if isinstance(normalized_result, QFDataArray):
            normalized_result = normalized_result.assign_coords(
                tickers=[tickers_mapping[t] for t in normalized_result.tickers.values])
        elif isinstance(normalized_result, PricesDataFrame):
            normalized_result = normalized_result.rename(columns=tickers_mapping)
        elif isinstance(normalized_result, PricesSeries):
            # Name of the PricesSeries can only contain strings
            if len(tickers) == 1:
                ticker = tickers[0]
                normalized_result = normalized_result.rename(ticker.name)
            else:
                normalized_result = normalized_result.rename(tickers_mapping)
        return normalized_result

    def _check_data_availibility(self, data_bundle, end_date, nr_of_bars, tickers):
        if data_bundle.shape[0] < nr_of_bars:
            tickers_as_strings = ", ".join(ticker.as_string() for ticker in tickers)
            raise ValueError(f"Not enough data points for tickers: {tickers_as_strings}, date: {end_date}. "
                             f"{nr_of_bars} Data points requested, {data_bundle.shape[0]} points available. "
                             f"Number of bars requested will increase data aggregation is needed.")

    def _aggregate_bars(self, data_array, fields, frequency: Frequency):
        """
        Function, which aggregates the data array for various dates and returns a new data array with data
        sampled with the given frequency.
        """

        # label with beginning of the bar for intraday, with end of bar for daily and lower frequency
        label = "right" if frequency <= Frequency.DAILY else "left"

        prices_list = []
        for field in fields:
            prices = data_array.loc[:, :, field].to_series().groupby(
                [pd.Grouper(freq=frequency.to_pandas_freq(), level=0, label=label, origin="start_day"),
                 pd.Grouper(level=1)])

            if field is PriceField.Open:
                prices = prices.first()
            elif field is PriceField.Close:
                prices = prices.last()
            elif field is PriceField.Low:
                prices = prices.min()
            elif field is PriceField.High:
                prices = prices.max()
            elif field is PriceField.Volume:
                prices = prices.sum()
            else:
                raise NotImplementedError(f"Unknown price field passed to the PresetDataProvider: {field}")

            prices = pd.concat({field: prices}, names=[FIELDS])
            prices_list.append(prices)

        data_array = QFDataArray.from_xr_data_array(
            pd.concat(prices_list).reorder_levels([DATES, TICKERS, FIELDS]).to_xarray())
        return data_array

    @staticmethod
    def _adjust_end_date(end_date: Optional[datetime]) -> datetime:
        end_date = end_date or datetime.now()
        return end_date + RelativeDelta(second=0, microsecond=0)
