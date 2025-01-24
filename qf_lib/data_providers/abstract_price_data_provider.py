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
import math
from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Union, Sequence, Dict, Optional

from numpy import nan
from pandas import concat
from pandas._libs.tslibs.offsets import to_offset
from pandas._libs.tslibs.timestamps import Timestamp

from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import RealTimer, SettableTimer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array


class AbstractPriceDataProvider(DataProvider, metaclass=ABCMeta):
    """
    Interface for data providers that supply historical data for various asset classes, including stocks, indices, and futures.

    This base class is designed for simple data providers, which are linked to a single data source (e.g., Quandl, Bloomberg, Yahoo).
    It defines the standard structure and methods that any specific data provider implementation must adhere to in order to access and retrieve historical market data.

    Notes:
        - When implementing the get_history method (which drivers a large portion of backtesting capabilities) careful consideration must be taken
        to ensure the data is returned in the expected format depending on the specific input tickers and fields.
        For Example:
            - isinstance(tickers, str) and isinstance(fields, str) it is expected to return a PriceSeries object
            - isinstance(tickers, str) and isinstance(fields, list) it is expected to return a PricesDataframe object
            - otherwise it is expected to return a QFDataArray object

    """

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY,
                  look_ahead_bias: Optional[bool] = False, **kwargs) -> \
            Union[None, PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Gets adjusted historical Prices (Open, High, Low, Close) and Volume

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            tickers for securities which should be retrieved
        fields: PriceField, Sequence[PriceField]
            fields of securities which should be retrieved
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        frequency: Frequency
            frequency of the data
        look_ahead_bias: False
            if set to False, no future data will be ever returned

        Returns
        -------
        None, PricesSeries, PricesDataFrame, QFDataArray
            If possible the result will be squeezed so that instead of returning QFDataArray (3-D structure),
            data of lower dimensionality will be returned. The results will be either an QFDataArray (with 3 dimensions:
            dates, tickers, fields), PricesDataFrame (with 2 dimensions: dates, tickers or fields.
            It is also possible to get 2 dimensions ticker and field if single date was provided), or PricesSeries
            with 1 dimension: dates. All the containers will be indexed with PriceField whenever possible
            (for example: instead of 'Close' column in the PricesDataFrame there will be PriceField.Close)
        """
        end_date = (end_date or self.timer.now()) + RelativeDelta(second=0, microsecond=0)
        start_date = self._adjust_start_date(start_date, frequency)
        got_single_date = self._got_single_date(start_date, end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, PriceField)

        fields_str = self._map_field_to_str(fields)
        container = self.get_history(tickers, fields_str, start_date, end_date, frequency,
                                     look_ahead_bias=look_ahead_bias, **kwargs)
        str_to_field_dict = self.str_to_price_field_map()

        # Map the specific fields onto the fields given by the str_to_field_dict
        if isinstance(container, QFDataArray):
            container = container.assign_coords(
                fields=[str_to_field_dict[field_str] for field_str in container.fields.values])
            normalized_result = normalize_data_array(
                container, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=True
            )
        else:
            normalized_result = PricesDataFrame(container).rename(columns=str_to_field_dict)
            if got_single_field:
                normalized_result = normalized_result.squeeze(axis=1)
            if got_single_ticker:
                normalized_result = normalized_result.squeeze(axis=0)

        return normalized_result

    @abstractmethod
    def price_field_to_str_map(self, *args) -> Dict[PriceField, str]:
        """
        Method has to be implemented in each data provider in order to be able to use get_price.
        Returns dictionary containing mapping between PriceField and corresponding string that has to be used by
        get_history method to get appropriate type of price series.

        Returns
        -------
        Dict[PriceField, str]
             mapping between PriceFields and corresponding strings
        """
        raise NotImplementedError()

    def historical_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                         fields: Union[PriceField, Sequence[PriceField]],
                         nr_of_bars: int, end_date: Optional[datetime] = None,
                         frequency: Frequency = None, **kwargs) -> Union[PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Returns the latest available data samples, which simply correspond to the last available <nr_of_bars> number
        of bars.

        In case of intraday data and N minutes frequency, the most recent data may not represent exactly N minutes
        (if the whole bar was not available at this time). The time ranges are always aligned to the market open time.
        Non-zero seconds and microseconds are in the above case omitted (the output at 11:05:10 will be exactly
        the same as at 11:05).

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            ticker or sequence of tickers of the securities
        fields: PriceField, Sequence[PriceField]
            PriceField or sequence of PriceFields of the securities
        nr_of_bars: int
            number of data samples (bars) to be returned.
            Note: while requesting more than one ticker, some tickers may have fewer than n_of_bars data points
        end_date: Optional[datetime]
            last date which should be considered in the query, the nr_of_bars that should be returned will always point
            to the time before end_date. The parameter is optional and if not provided, the end_date will point to the
            current user time.
        frequency
            frequency of the data

        Returns
        --------
        PricesSeries, PricesDataFrame, QFDataArray
        """
        frequency = frequency or self.frequency or Frequency.DAILY
        assert frequency >= Frequency.DAILY, "Frequency lower than daily is not supported by the Data Provider"
        assert nr_of_bars > 0, "Numbers of data samples should be a positive integer"
        end_date = self.get_end_date_without_look_ahead(end_date, frequency)

        # Add additional days to ensure that any data absence will not impact the number of bars which will be returned
        start_date = self._compute_start_date(nr_of_bars, end_date, frequency)
        start_date = self._adjust_start_date(start_date, frequency)

        container = self.get_price(tickers, fields, start_date, end_date, frequency)
        missing_bars = nr_of_bars - container.shape[0]

        # In case if a bigger margin is necessary to get the historical price, shift the start date and download prices
        # once again
        if missing_bars > 0:
            start_date = self._compute_start_date(missing_bars, start_date, frequency)
            container = self.get_price(tickers, fields, start_date, end_date, frequency)

        num_of_dates_available = container.shape[0]
        if num_of_dates_available < nr_of_bars:
            if isinstance(tickers, Ticker):
                tickers_as_strings = tickers.as_string()
            else:
                tickers_as_strings = ", ".join(ticker.as_string() for ticker in tickers)
            raise ValueError(f"Not enough data points for \ntickers: {tickers_as_strings} \ndate: {end_date}."
                             f"\n{nr_of_bars} Data points requested, \n{num_of_dates_available} Data points available.")

        if isinstance(container, QFDataArray):
            return container.isel(dates=slice(-nr_of_bars, None))
        else:
            return container.tail(nr_of_bars)

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Optional[Frequency] = None,
                                 end_time: Optional[datetime] = None) -> Union[float, QFSeries]:
        """
        Gets the latest available price for given assets as of end_time.

        Parameters
        -----------
        tickers: Ticker, Sequence[Ticker]
            tickers of the securities which prices should be downloaded
        frequency: Frequency
            frequency of the data
        end_time: datetime
            date which should be used as a base to compute the last available price. The parameter is optional and if
            not provided, the end_date will point to the current user time.

        Returns
        -------
        float, pandas.Series
            last_prices series where:
            - last_prices.name contains a date of current prices,
            - last_prices.index contains tickers
            - last_prices.data contains latest available prices for given tickers
        """
        frequency = frequency or self.frequency
        if isinstance(self.timer, RealTimer):
            return self._last_available_price(tickers, frequency, end_time)

        if frequency is None:
            raise AttributeError(f"Data provider {self.__class__.__name__} has no set frequency. Please set it before "
                                 f"running a simulation with SettableTimer.")

        if isinstance(self.timer, SettableTimer) and frequency == Frequency.DAILY:
            return self._last_available_price_settable_timer_daily(tickers, frequency, end_time)
        if isinstance(self.timer, SettableTimer) and frequency > Frequency.DAILY:
            return self._last_available_price_settable_timer_intraday(tickers, frequency, end_time)
        else:
            raise NotImplementedError("TODO")

    def str_to_price_field_map(self) -> Dict[str, PriceField]:
        """
        Inverse of price_field_to_str_map.
        """
        field_str_dict = self.price_field_to_str_map()
        inv_dict = {v: k for k, v in field_str_dict.items()}
        return inv_dict

    @staticmethod
    def _get_valid_latest_available_prices(start_date: datetime, tickers: Sequence[Ticker], open_prices: QFDataFrame,
                                           close_prices: QFDataFrame) -> QFSeries:
        latest_available_prices = []
        for ticker in tickers:
            last_valid_open_price_date = open_prices.loc[:, ticker].last_valid_index() or start_date
            last_valid_close_price_date = close_prices.loc[:, ticker].last_valid_index() or start_date

            try:
                if last_valid_open_price_date > last_valid_close_price_date:
                    price = open_prices.loc[last_valid_open_price_date, ticker]
                else:
                    price = close_prices.loc[last_valid_close_price_date, ticker]
            except KeyError:
                price = nan

            latest_available_prices.append(price)

        latest_available_prices_series = PricesSeries(data=latest_available_prices, index=tickers)
        return latest_available_prices_series

    @staticmethod
    def _compute_start_date(nr_of_bars_needed: int, end_date: datetime, frequency: Frequency):
        margin = 10 if frequency <= Frequency.DAILY else 1
        nr_of_days_to_go_back = math.ceil(nr_of_bars_needed * 365 / frequency.value) + margin

        # In case if the end_date points to saturday, sunday or monday shift it to saturday midnight
        if end_date.weekday() in (0, 5, 6):
            end_date = end_date - RelativeDelta(weeks=1, weekday=5, hour=0, minute=0, microsecond=0)

        # Remove the time part and leave only days in order to align the start date to match the market open time
        # in case of intraday data, e.g. if the market opens at 13:30, the bars will also start at 13:30
        start_date = end_date - RelativeDelta(days=nr_of_days_to_go_back, hour=0, minute=0, second=0, microsecond=0)
        return start_date

    def _adjust_start_date(self, start_date: datetime, frequency: Frequency):
        if frequency > Frequency.DAILY:
            frequency_delta = to_offset(frequency.to_pandas_freq()).delta.value
            new_start_date = Timestamp(math.ceil(Timestamp(start_date).value / frequency_delta) * frequency_delta) \
                .to_pydatetime()
            if new_start_date != start_date:
                self.logger.info(f"Adjusting the starting date to {new_start_date} from {start_date}.")
        else:
            new_start_date = start_date + RelativeDelta(hour=0, minute=0, second=0, microsecond=0)
            if new_start_date.date() != start_date.date():
                self.logger.info(f"Adjusting the starting date to {new_start_date} from {start_date}.")

        return new_start_date

    @staticmethod
    def _got_single_date(start_date: datetime, end_date: datetime, frequency: Frequency):
        return (start_date + frequency.time_delta()).date() > end_date.date() if frequency <= Frequency.DAILY else \
            (start_date + frequency.time_delta() >= end_date)

    def _map_field_to_str(
            self, fields: Union[None, PriceField, Sequence[PriceField]]) \
            -> Union[None, str, Sequence[str]]:
        """
        The method maps enum to sting that is recognised by the specific database.

        Parameters
        ----------
        fields
            fields of securities which should be retrieved

        Returns
        -------
        str, Sequence[str]
            String representation of the field or fields that corresponds the API provided by a specific data provider
            Depending on the input it returns:
            None -> None
            PriceField -> str
            Sequence[PriceField] -> List[str]
        """
        if fields is None:
            return None

        field_str_dict = self.price_field_to_str_map()

        if self._is_single_price_field(fields):
            if fields in field_str_dict:
                return field_str_dict[fields]
            else:
                raise LookupError("Field {} is not recognised by the data provider. Available Fields: {}"
                                  .format(fields, list(field_str_dict.keys())))

        result = []
        for field in fields:
            if field in field_str_dict:
                result.append(field_str_dict[field])
            else:
                raise LookupError("Field {} is not recognised by the data provider. Available Fields: {}"
                                  .format(fields, list(field_str_dict.keys())))
        return result

    @staticmethod
    def _is_single_price_field(fields: Union[None, PriceField, Sequence[PriceField]]):
        return fields is not None and isinstance(fields, PriceField)

    def _last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency,
                              end_time: Optional[datetime] = None):

        end_time = self.get_end_date_without_look_ahead(end_time, frequency)
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        if not tickers:
            return nan if got_single_ticker else PricesSeries()

        frequency = frequency or Frequency.DAILY
        assert frequency >= Frequency.DAILY, "Frequency lower then daily is not supported by the " \
                                             "get_last_available_price function"

        start_date = self._compute_start_date(5, end_time, frequency)
        start_date = self._adjust_start_date(start_date, frequency)

        open_prices = self.get_price(tickers, PriceField.Open, start_date, end_time, frequency)
        close_prices = self.get_price(tickers, PriceField.Close, start_date, end_time, frequency)

        latest_available_prices_series = self._get_valid_latest_available_prices(start_date, tickers, open_prices,
                                                                                 close_prices)
        return latest_available_prices_series.iloc[0] if got_single_ticker else latest_available_prices_series

    def _last_available_price_settable_timer_daily(self, tickers: Union[Ticker, Sequence[Ticker]],
                                                   frequency: Frequency = None,
                                                   end_time: Optional[datetime] = None) -> Union[float, QFSeries]:
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        if not tickers:
            return nan if got_single_ticker else PricesSeries()

        frequency = frequency or Frequency.DAILY
        end_time = end_time or self.timer.now()
        end_date_without_look_ahead = self.get_end_date_without_look_ahead(end_time, frequency)

        last_prices = self._last_available_price(tickers, frequency, end_date_without_look_ahead)

        latest_market_open = self._get_last_available_market_event(end_time, MarketOpenEvent)
        if end_date_without_look_ahead < latest_market_open:
            current_open_prices = self.get_price(tickers, PriceField.Open, latest_market_open,
                                                 latest_market_open, frequency, look_ahead_bias=True)
            last_prices = concat([last_prices, current_open_prices], axis=1).ffill(axis=1)
            last_prices = last_prices.iloc[:, -1]

        return last_prices.iloc[0] if got_single_ticker else last_prices

    def _last_available_price_settable_timer_intraday(self, tickers: Union[Ticker, Sequence[Ticker]],
                                                      frequency: Frequency = None,
                                                      end_time: Optional[datetime] = None) -> Union[float, QFSeries]:

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        if not tickers:
            return nan if got_single_ticker else PricesSeries()
        frequency = frequency or Frequency.MIN_1
        current_time = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_time = end_time or current_time
        end_date_without_look_ahead = self.get_end_date_without_look_ahead(end_time, frequency)

        if current_time <= end_time:
            last_prices = self._last_available_price(tickers, frequency, end_date_without_look_ahead)
            current_open_prices = self.get_price(tickers, PriceField.Open,
                                                 start_date=end_date_without_look_ahead + frequency.time_delta(),
                                                 end_date=end_date_without_look_ahead + frequency.time_delta(),
                                                 frequency=frequency, look_ahead_bias=True)
        else:
            last_prices = self._last_available_price(tickers, frequency,
                                                     end_date_without_look_ahead - frequency.time_delta())
            current_open_prices = self.get_price(tickers, PriceField.Open,
                                                 start_date=end_date_without_look_ahead,
                                                 end_date=end_date_without_look_ahead,
                                                 frequency=frequency, look_ahead_bias=True)

        last_prices = concat([last_prices, current_open_prices], axis=1).ffill(axis=1)
        last_prices = last_prices.iloc[:, -1]

        return last_prices.iloc[0] if got_single_ticker else last_prices
