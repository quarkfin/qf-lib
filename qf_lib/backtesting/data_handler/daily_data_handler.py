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
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
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


class DailyDataHandler(DataHandler):

    def _check_frequency(self, frequency):
        if frequency and frequency > Frequency.DAILY:
            raise ValueError("Frequency higher than daily is not supported by DailyDataHandler.")

    def historical_price(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
            nr_of_bars: int, frequency: Frequency = None) -> Union[PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Returns the latest available data samples corresponding to the nr_of_bars.

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

        frequency = frequency or self.fixed_data_provider_frequency or Frequency.DAILY

        nr_of_days_to_go_back = int(nr_of_bars * (365 / 252) + 10)
        end_date = self._get_end_date_without_look_ahead()
        start_date = end_date - RelativeDelta(days=nr_of_days_to_go_back)

        container = self.data_provider.get_price(tickers, fields, start_date, end_date, frequency)

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

        It accesses the latest fully available bar as of "today", that is: if a bar wasn't closed for today yet,
        then all the PriceFields (e.g. OPEN) will concern data from yesterday.
        """
        frequency = frequency or self.fixed_data_provider_frequency or Frequency.DAILY
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_date)
        return self.data_provider.get_price(tickers, fields, start_date, end_date_without_look_ahead,
                                            frequency)

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]], start_date: datetime,
            end_date: datetime = None, frequency: Frequency = None, **kwargs) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Runs DataProvider.get_history(...) but before makes sure that the query doesn't concern data from the future.

        See: DataProvider.get_history(...)
        """
        frequency = frequency or self.fixed_data_provider_frequency or Frequency.DAILY
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_date)
        return self.data_provider.get_history(tickers, fields, start_date, end_date_without_look_ahead, frequency)

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                                 frequency: Frequency = None) -> Union[float, pd.Series]:
        """
        Gets the latest available price for given assets (even if the full bar is not yet available).
        The frequency parameter is always casted into daily frequency, to represent the most recent price.

        If "now" is at or after the market OPEN already, then the OPEN price will be returned.
        If "now" is after the market CLOSE, the close price will be returned.
        Always the latest available data will be returned (thus None or a Series of pd.nans will never be returned).

        Returns
        -------
        last_prices
            Series where:
            - last_prices.name contains a date of current prices,
            - last_prices.index contains tickers
            - last_prices.data contains latest available prices for given tickers
        """

        return self._get_single_date_price(tickers, nans_allowed=False, frequency=Frequency.DAILY)

    def get_current_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                          frequency: Frequency = None) -> Union[float, pd.Series]:
        """
        Works just like get_last_available_price() but it can return NaNs if data is not available at the current
        moment (e.g. it returns NaN on a non-trading day or when current time is different than the time of MarketOpen
        or MarketClose).

        The frequency parameter is always casted into daily frequency, to represent the most recent price.

        If "now" is at the market OPEN and the price is available (trading day) the OPEN price will be returned.
        If "now" is at the market CLOSE and the price is available (trading day) the CLOSE price will be returned.
        In other cases (e.g. someone tries to get current price on a non-trading day or current time is different
        than MarketOpen or MarketClose) None will be returned (or the Series of pd.nan if multiple
        tickers were supplied).

        Returns
        -------
        current_prices
            Series where:
            - current_prices.name contains a date of current prices,
            - current_prices.index contains tickers
            - current_prices.data contains latest available prices for given tickers
        """
        return self._get_single_date_price(tickers, nans_allowed=True, frequency=Frequency.DAILY)

    def get_current_bar(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None) \
            -> Union[pd.Series, pd.DataFrame]:
        """
        Gets the current bar(s) for given Ticker(s). If the bar is not available yet (e.g. before the market close),
        None is returned.

        If the request for single Ticker was made, then the result is a pandas.Series indexed with PriceFields (OHLCV).
        If the request for multiple Tickers was made, then the result has Tickers as an index and PriceFields
        as columns.

        Normally on working days the method will return non-empty bars in the time between (inclusive)
        MarketCloseEvent and midnight (exclusive).

        On non-working days or on working days in the time between midnight (inclusive) and MarketClose (exclusive),
        e.g. 12:00, the returned bars will contain Nones as values.
        """
        if not tickers:
            return pd.Series()

        frequency = frequency or self.fixed_data_provider_frequency or Frequency.DAILY

        tickers, was_single_ticker_provided = convert_to_list(tickers, Ticker)

        current_datetime = self.timer.now()

        if self.time_helper.datetime_of_latest_market_event(MarketCloseEvent) < current_datetime:
            last_available_bars = pd.DataFrame(index=tickers, columns=PriceField.ohlcv())
        else:
            current_date = self._zero_out_time_component(current_datetime)
            start_date = current_date - RelativeDelta(days=7)

            prices_data_array = self.get_price(tickers=tickers, fields=PriceField.ohlcv(), start_date=start_date,
                                               end_date=current_date, frequency=frequency)  # type: QFDataArray
            try:
                last_available_bars = prices_data_array.loc[current_date].to_pandas()
            except KeyError:
                return pd.DataFrame(index=tickers, columns=PriceField.ohlcv())

        if was_single_ticker_provided:
            last_available_bars = last_available_bars.iloc[0, :]

        return last_available_bars

    def _get_end_date_without_look_ahead(self, end_date=None):
        # Consider the time of latest market close event
        # If end_date is None, it is assumed that it is equal to latest_available_market_close

        latest_available_market_close = self.time_helper.datetime_of_latest_market_event(MarketCloseEvent)
        end_date = end_date + RelativeDelta(second=0, microsecond=0) if end_date is not None else \
            latest_available_market_close

        return min(latest_available_market_close, end_date)

    def _get_single_date_price(
            self, tickers: Union[Ticker, Sequence[Ticker]], nans_allowed: bool, frequency: Frequency = Frequency.DAILY) \
            -> Union[float, pd.Series]:
        tickers, was_single_ticker_provided = convert_to_list(tickers, Ticker)

        # if an empty tickers list was supplied then return an empty result
        if not tickers:
            return pd.Series()

        # Compute the time ranges, used further by the get_price function
        current_datetime = self.timer.now()

        # We download the prices since the last 7 days. In case of getting the last available price, we assume that
        # within each 7 consecutive days, at least one price will occur. If not, in case e.g. future contracts, we
        # assume that the contract ended and we need to e.g. close the position for this ticker in the portfolio, if
        # open.
        start_date = current_datetime - RelativeDelta(days=7)
        current_date = self._zero_out_time_component(current_datetime)

        price_fields = [PriceField.Open, PriceField.Close]

        prices_data_array = self.data_provider.get_price(tickers, price_fields, start_date, current_date,
                                                         frequency)
        prices_df = self._data_array_to_dataframe(prices_data_array)

        prices_df = prices_df.loc[:current_datetime]

        try:
            prices_series = prices_df.loc[current_datetime, :]
        except KeyError:
            prices_series = pd.Series(index=tickers)

        prices_series.name = "Current asset prices"

        if not nans_allowed:
            # fill NaNs with latest available prices
            last_available_close_prices = prices_df.apply(func=lambda series: series.asof(current_datetime))

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

    def _zero_out_time_component(self, current_datetime):
        # below the time component is zeroed-out because most of data providers expect it to be so
        current_date = datetime(current_datetime.year, current_datetime.month, current_datetime.day)
        return current_date

    def _data_array_to_dataframe(self, prices_data_array: QFDataArray):
        """
        Converts a QFDataArray into a DataFrame by removing the "Price Field" axis.

        In order to remove it open and close prices get different time component in their corresponding datetimes
        (open prices will get the time of `MarketOpenEvent` and close prices will get the time of `MarketCloseEvent`).
        """
        original_dates = prices_data_array.dates.to_index()

        market_open_datetimes = [price_datetime + MarketOpenEvent.trigger_time() for price_datetime in original_dates]
        market_close_datetimes = [price_datetime + MarketCloseEvent.trigger_time() for price_datetime in original_dates]

        new_dates = set(market_open_datetimes + market_close_datetimes)

        prices_df = PricesDataFrame(index=new_dates, columns=prices_data_array.tickers)
        prices_df.loc[market_open_datetimes, :] = prices_data_array.loc[:, :, PriceField.Open].values
        prices_df.loc[market_close_datetimes, :] = prices_data_array.loc[:, :, PriceField.Close].values

        prices_df.sort_index(inplace=True)
        return prices_df
