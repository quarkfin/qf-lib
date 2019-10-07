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
from typing import Union, Sequence

import pandas as pd

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class IntradayDataHandler(DataHandler):

    def _check_frequency(self, frequency):
        if frequency and frequency <= Frequency.DAILY:
            raise ValueError("Only frequency higher than daily is supported by IntradayDataHandler.")

    def historical_price(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
            nr_of_bars: int, frequency: Frequency = None) -> Union[PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Returns the latest available data samples. In case of N minutes frequency, the most recent data may not
        represent exactly N minutes (if the whole bar was not available at this time). The time ranges are always
        aligned to the market open time.

        E.g. In case of market open time equal to 10:30, the historical_price at 11:05 with frequency set to
        15 minutes and 3 bars, the data samples corresponding to the following bars will be returned:
        10:30 - 10:45  (inclusive; full 15 minutes bar)
        10:45 - 11:00
        11:00 - 11:05  (inclusive; only 5 minutes bar)
        The series is indexed with the open time (left side of the time range).

        Non-zero seconds and microseconds are in the above case omitted (the output at 11:05:10 will be exactly
        the same as at 11:05).

        Parameters
        ----------
        tickers
            ticker or sequence of tickers of the securities
        fields
            PriceField or sequence of PriceFields of the securities
        nr_of_bars
            number of data samples (bars) to be returned.
            Note: while requesting more than one ticker, some tickers may have fewer than n_of_bars data points
        frequency
            frequency of the data
        """

        frequency = frequency or self.fixed_data_provider_frequency or Frequency.MIN_1

        days_per_year = Frequency.DAILY.occurrences_in_year
        bars_per_year = frequency.occurrences_in_year
        bars_per_day = int(bars_per_year / days_per_year)

        # Add 5 days to ensure that any data absence will not impact the number of bars which will be returned
        nr_of_days_to_go_back = int(nr_of_bars / bars_per_day + 5)

        end_date = self._get_end_date_without_look_ahead()

        # Remove the time part and leave only days in order to align the start date to match the market open time
        # E.g. if the market opens at 13:30, the bars will also start at 13:30
        start_date = end_date - RelativeDelta(days=nr_of_days_to_go_back, hour=0, minute=0, second=0, microsecond=0)

        container = self.price_data_provider.get_price(tickers, fields, start_date, end_date, frequency)

        num_of_dates_available = container.shape[0]
        if num_of_dates_available < nr_of_bars:
            if isinstance(tickers, Ticker):
                tickers_as_strings = tickers.as_string()
            else:
                tickers_as_strings = ", ".join(ticker.as_string() for ticker in tickers)
            raise ValueError("Not enough data points for \ntickers: {} \ndate: {}."
                             "\n{} Data points requested, \n{} Data points available.".format(
                tickers_as_strings, end_date, nr_of_bars, num_of_dates_available))

        if isinstance(container, QFDataArray):
            return container.isel(dates=slice(-nr_of_bars, None))
        else:
            return container.tail(nr_of_bars)  # type: Union[PricesSeries, PricesDataFrame]

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY) -> \
            Union[PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Runs DataProvider.get_price(...) but before makes sure that the query doesn't concern data from
        the future.
        """
        frequency = frequency or self.fixed_data_provider_frequency or Frequency.MIN_1
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_date)
        return self.price_data_provider.get_price(tickers, fields, start_date, end_date_without_look_ahead,
                                                  frequency)

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]], start_date: datetime,
            end_date: datetime = None, frequency: Frequency = None, **kwargs) ->\
            Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Runs DataProvider.get_history(...) but before makes sure that the query doesn't concern data from the future.

        See: DataProvider.get_history(...)
        """
        frequency = frequency or self.fixed_data_provider_frequency or Frequency.MIN_1
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_date)
        return self.price_data_provider.get_history(tickers, fields, start_date, end_date_without_look_ahead, frequency)

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                                 frequency: Frequency = None) -> Union[float, pd.Series]:
        """
        Gets the latest available price for given assets, even if the full bar is not yet available.

        The frequency parameter is always casted into 1 minute frequency, to represent the most recent price.

        It returns the CLOSE price of the last available bar. If "now" is after the market OPEN, and before the market
        CLOSE, the last available price is equal to the current price (CLOSE price of the bar, which right bound is
        equal to "now"). If the market did not open yet, the last available CLOSE price will be returned.
        Non-zero seconds or microseconds values are omitted (e.g. 13:40:01 is always treated as 13:40:00).

        Returns
        -------
        last_prices
            Series where:
            - last_prices.name contains a date of current prices,
            - last_prices.index contains tickers
            - last_prices.data contains latest available prices for given tickers
        """
        return self._get_single_date_price(tickers, nans_allowed=False, frequency=Frequency.MIN_1)

    def get_current_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                                 frequency: Frequency = None) -> Union[float, pd.Series]:
        """
        Works just like get_last_available_price() but it can return NaNs if data is not available at the current
        moment (e.g. it returns NaN on a non-trading day).

        The frequency parameter is always casted into 1 minute frequency, to represent the most recent price.

        If the frequency parameter is an intraday frequency, the CLOSE price of the currently available bar will be
        returned.
        E.g. for 1 minute frequency, at 13:00 (if the market opens before 13:00), the CLOSE price of the
        12:59 - 13:00 bar will be returned.
        If "now" contains non-zero seconds or microseconds, None will be returned.

        Returns
        -------
        current_prices
            Series where:
            - current_prices.name contains a date of current prices,
            - current_prices.index contains tickers
            - current_prices.data contains latest available prices for given tickers
        """
        return self._get_single_date_price(tickers, nans_allowed=True, frequency=Frequency.MIN_1)

    def get_current_bar(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None) \
            -> Union[pd.Series, pd.DataFrame]:
        """
        Gets the current bar(s) for given Ticker(s). If the bar is not available yet, None is returned.

        If the request for single Ticker was made, then the result is a pandas.Series indexed with PriceFields (OHLCV).
        If the request for multiple Tickers was made, then the result has Tickers as an index and PriceFields
        as columns.

        In case of N minutes frequency, the current bar can be returned in the time between (inclusive) N minutes
        after MarketOpenEvent and the MarketCloseEvent).

        E.g. for 1 minute frequency, at 13:00 (if the market opens before 13:00), the 12:59 - 13:00 bar will be
        returned. In case of 15 minutes frequency, when the market opened less then 15 minutes ago, Nones will be
        returned. If current time ("now") contains non-zero seconds or microseconds, Nones will be returned.
        """
        if not tickers:
            return pd.Series()

        frequency = frequency or self.fixed_data_provider_frequency or Frequency.MIN_1

        tickers, was_single_ticker_provided = convert_to_list(tickers, Ticker)

        current_datetime = self.timer.now()

        start_date = current_datetime - frequency.time_delta()
        prices_data_array = self.get_price(tickers=tickers, fields=PriceField.ohlcv(), start_date=start_date,
                                           end_date=current_datetime, frequency=frequency)
        try:
            last_available_bars = prices_data_array.loc[start_date].to_pandas()
        except KeyError:
            return pd.DataFrame(index=tickers, columns=PriceField.ohlcv())

        if was_single_ticker_provided:
            last_available_bars = last_available_bars.iloc[0, :]

        return last_available_bars

    def _get_end_date_without_look_ahead(self, end_date=None):
        """
        Consider only the meaningful part of the date time (as the data can be gather at most with minutely
        frequency, delete the seconds and microseconds time part). Moreover, the `end date` is always exclusive,
        therefore it is only necessary to get the minimum of current time and the end date.
        If end_date is None, it is assumed that it is equal to current time.
        """

        current_time = self.timer.now() + RelativeDelta(second=0, microsecond=0)
        end_date = end_date + RelativeDelta(second=0, microsecond=0) if end_date is not None else current_time

        return min(current_time, end_date)

    def _get_single_date_price(
            self, tickers: Union[Ticker, Sequence[Ticker]], nans_allowed: bool, frequency: Frequency = Frequency.DAILY)\
            -> Union[float, pd.Series]:
        tickers, was_single_ticker_provided = convert_to_list(tickers, Ticker)

        # if an empty tickers list was supplied then return an empty result
        if not tickers:
            return pd.Series()

        current_datetime = self.timer.now()

        # Calculate the time ranges and start date, used further by the get_price function.

        # The time range denote the current_datetime +- 1 range. The current price is represented as the close price of
        # (time_range_start, current_datetime) range, labeled using the time_range_start value in most of the cases.
        # The only exception is the price at the market open - in this case we do not have the bar directly leading up
        # to market open time. Thus, the open price from the time range (current_datetime, time_range_end) is used to
        # denote the price.

        time_range_start = current_datetime - frequency.time_delta()
        time_range_end = current_datetime + frequency.time_delta()

        # The start date is used to download older data, in case if there is no price available currently and we are
        # interested in the last available one (nans_allowed = False). Therefore we look a few days in the past in this
        # case. Otherwise, the time_range_start time is used.

        download_start_date = time_range_start if nans_allowed else \
            current_datetime - RelativeDelta(days=5, hour=0, minute=0, second=0)

        price_fields = [PriceField.Open, PriceField.Close]

        prices_data_array = self.price_data_provider.get_price(tickers, price_fields, download_start_date,
                                                               time_range_end, frequency)
        prices_df = self._data_array_to_dataframe(prices_data_array, frequency)

        prices_df = prices_df.loc[:current_datetime]

        # Access the price bar starting at time_range_start and ending at current_datetime
        try:
            prices_series = prices_df.loc[time_range_start, :]
        except KeyError:
            prices_series = pd.Series(index=tickers)

        prices_series.name = "Current asset prices"

        if not nans_allowed:
            # fill NaNs with latest available prices
            last_available_close_prices = prices_df.apply(func=lambda series: series.asof(time_range_start))

            if not last_available_close_prices.empty:
                unavailable_prices_tickers = prices_series.isnull()
                prices_series.loc[unavailable_prices_tickers] = \
                    last_available_close_prices.loc[unavailable_prices_tickers]

            prices_series.name = "Last available asset prices"

        prices_series = cast_series(prices_series, pd.Series)
        if was_single_ticker_provided:
            return prices_series[0]
        else:
            return prices_series

    def _data_array_to_dataframe(self, prices_data_array: QFDataArray, frequency: Frequency):
        """
        Converts a QFDataArray into a DataFrame by removing the "Price Field" axis.

        Every index (e.g. 15:00) denotes the close price of the time range beginning at this time (15:00 - 15:01)
        The only exception is the time range 1 minute before market open (e.g. 9:29 - 9:30 if market opens 9:30). The
        price for this time range, denotes the OPEN price of 9:30 - 9:31.
        """
        original_dates = list(prices_data_array.dates.to_index())
        market_open_datetimes = [price_datetime for price_datetime in original_dates if
                                 price_datetime + MarketOpenEvent.trigger_time() == price_datetime]
        shifted_open_datetimes = [price_datetime - frequency.time_delta() for price_datetime in
                                  market_open_datetimes]

        new_dates = list(set(shifted_open_datetimes + original_dates))
        prices_df = PricesDataFrame(index=new_dates, columns=prices_data_array.tickers)

        prices_df.loc[shifted_open_datetimes, :] = \
            prices_data_array.loc[market_open_datetimes, :, PriceField.Open].values
        prices_df.loc[original_dates, :] = prices_data_array.loc[original_dates, :, PriceField.Close].values

        prices_df.sort_index(inplace=True)
        return prices_df
