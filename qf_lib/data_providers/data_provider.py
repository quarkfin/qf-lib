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
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union, Sequence, Type, Set, Dict, Optional

from numpy import nan
from pandas._libs.tslibs.offsets import to_offset
from pandas._libs.tslibs.timestamps import Timestamp

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries


class DataProvider(object, metaclass=ABCMeta):
    """ An interface for data providers (for example AbstractPriceDataProvider or GeneralPriceProvider). """

    frequency = None

    def __init__(self):
        self.logger = qf_logger.getChild(self.__class__.__name__)

    @abstractmethod
    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = None) -> Union[
                        None, PricesSeries, PricesDataFrame, QFDataArray]:
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
        pass

    @abstractmethod
    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[None, str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, frequency: Frequency = None, **kwargs) -> Union[
                QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical attributes (fields) of different securities (tickers).

        All the duplicate fields and tickers will be removed (the first occurrence will remain). This is crucial
        for having the expected behavior with using label-based indices. E.g. let's assume there is a duplicate ticker
        'SPX Index' in tickers list and the result data frame has two columns 'SPX Index'. Then when someone
        runs result.loc[:, 'SPX Index'], he expects to get a series of 'SPX Index' values. However
        he'll get a data frame with two columns, both named 'SPX Index'.
        If someone insists on keeping duplicate values in index/columns, then it's possible to reindex the result
        (e.g. result.reindex(columns=tickers)).

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            tickers for securities which should be retrieved
        fields: None, str, Sequence[str]
            fields of securities which should be retrieved. If None, all available fields will be returned
            (only supported by few DataProviders)
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        frequency: Frequency
            frequency of the data
        kwargs
            kwargs should not be used on the level of AbstractDataProvider. They are here to provide a common interface
            for all data providers since some of the specific data providers accept additional arguments

        Returns
        -------
        QFSeries, QFDataFrame, QFDataArray
            If possible the result will be squeezed, so that instead of returning QFDataArray, data of lower
            dimensionality will be returned. The results will be either an QFDataArray (with 3 dimensions: date, ticker,
            field), a QFDataFrame (with 2 dimensions: date, ticker or field; it is also possible to get 2 dimensions
            ticker and field if single date was provided) or QFSeries (with 1 dimensions: date).
            If no data is available in the database or an non existing ticker was provided an empty structure
            (QFSeries, QFDataFrame or QFDataArray) will be returned returned.
        """
        pass

    @abstractmethod
    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        """
        Returns classes of tickers which are supported by this DataProvider.
        """
        pass

    @abstractmethod
    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, Union[QFSeries, QFDataFrame]]:
        """
        Returns tickers of futures contracts, which belong to the same futures contract chain as the provided ticker
        (tickers), along with their expiration dates in form of a QFSeries or QFDataFrame.

        Parameters
        ----------
        tickers: FutureTicker, Sequence[FutureTicker]
            tickers for which should the future chain tickers be retrieved
        expiration_date_fields: ExpirationDateField, Sequence[ExpirationDateField]
            field that should be downloaded as the expiration date field, by default last tradeable date

        Returns
        -------
        Dict[FutureTicker, Union[QFSeries, QFDataFrame]]
            Returns a dictionary, which maps Tickers to QFSeries, consisting of the expiration dates of Future
            Contracts: Dict[FutureTicker, Union[QFSeries, QFDataFrame]]]. The QFSeries' / QFDataFrames contain the
            specific Tickers, which belong to the corresponding futures family, same as the FutureTicker, and are
            indexed by the expiration dates of the specific future contracts.
        """
        pass

    def historical_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                         fields: Union[PriceField, Sequence[PriceField]],
                         nr_of_bars: int, end_date: Optional[datetime] = None,
                         frequency: Frequency = None) -> Union[PricesSeries, PricesDataFrame, QFDataArray]:
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
        # frequency = frequency or self.default_frequency
        assert frequency >= Frequency.DAILY, "Frequency lower than daily is not supported by the Data Provider"
        assert nr_of_bars > 0, "Numbers of data samples should be a positive integer"
        end_date = datetime.now() if end_date is None else end_date

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

    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency,
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
        end_time = datetime.now() if end_time is None else end_time
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        if not tickers:
            return nan if got_single_ticker else PricesSeries()

        assert frequency >= Frequency.DAILY, "Frequency lower then daily is not supported by the " \
                                             "get_last_available_price function"

        start_date = self._compute_start_date(5, end_time, frequency)
        start_date = self._adjust_start_date(start_date, frequency)

        open_prices = self.get_price(tickers, PriceField.Open, start_date, end_time, frequency)
        close_prices = self.get_price(tickers, PriceField.Close, start_date, end_time, frequency)

        latest_available_prices_series = self._get_valid_latest_available_prices(start_date, tickers, open_prices, close_prices)
        return latest_available_prices_series.iloc[0] if got_single_ticker else latest_available_prices_series

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
        return start_date.date() == end_date.date() if frequency <= Frequency.DAILY else \
                (start_date + frequency.time_delta() > end_date)

    def __str__(self):
        return self.__class__.__name__
