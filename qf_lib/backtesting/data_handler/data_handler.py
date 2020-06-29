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
from abc import abstractmethod
from datetime import datetime
from typing import Union, Sequence, Type, Optional, Dict

import pandas as pd

from qf_lib.backtesting.events.time_event.regular_time_event.regular_time_event import RegularTimeEvent
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider


class DataHandler(DataProvider):
    """
    DataHandler is a wrapper which can be used with any AbstractPriceDataProvider in both live and backtest
    environment. It makes sure that data "from the future" is not passed into components in the backtest environment.

    DataHandler should be used by all the Backtester's components (even in the live trading setup).

    The goal of a DataHandler is to provide backtester's components with financial data. It also makes sure that
    no data from the future (relative to a "current" time of a backtester) is being accessed, that is: that there
    is no look-ahead bias.

    Parameters
    -----------
    data_provider: DataProvider
        the underlying data provider
    timer: Timer
        timer used to keep track of the data "from the future"
    """

    def __init__(self, data_provider: DataProvider, timer: Timer):
        self.data_provider = data_provider

        self._check_frequency(data_provider.frequency)
        self.fixed_data_provider_frequency = data_provider.frequency  # type: Optional[Frequency]

        self.timer = timer
        self.time_helper = _DataHandlerTimeHelper(timer)

        self.is_optimised = False

    def use_data_bundle(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                        start_date: datetime, end_date: datetime, frequency: Frequency = Frequency.DAILY):
        """
        Optimises running of the backtest. All the data will be downloaded before the backtest.
        Note that requesting during the backtest any other ticker or price field than the ones in the params
        of this function will result in an Exception.

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            ticker or sequence of tickers of the securities
        fields: PriceField, Sequence[PriceField]
            PriceField or sequence of PriceFields of the securities
        start_date: datetime
            initial date that should be downloaded
        end_date: datetime
            last date that should be downloaded
        frequency
            frequency of the data
        """
        assert not self.is_optimised, "Multiple calls on use_data_bundle() are forbidden"

        tickers, _ = convert_to_list(tickers, Ticker)
        fields, _ = convert_to_list(fields, PriceField)

        self._check_frequency(frequency)
        self.fixed_data_provider_frequency = frequency

        self.data_provider = PrefetchingDataProvider(self.data_provider, tickers, fields, start_date, end_date,
                                                     frequency)

        self.is_optimised = True

    @abstractmethod
    def _check_frequency(self, frequency):
        """
        Verify if the provided frequency is compliant with the type of Data Handler used.
        """
        pass

    @abstractmethod
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

        Returns
        --------
        PricesSeries, PricesDataFrame, QFDataArray
        """
        pass

    @abstractmethod
    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = None) -> \
            Union[PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Acceses prices, using the DataProvider get_price functionality, but before makes sure that the query doesn't
        concern data from the future.

        See Also
        --------
        DataProvider.get_price
        """
        pass

    @abstractmethod
    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]], start_date: datetime,
            end_date: datetime = None, frequency: Frequency = None, **kwargs) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Runs DataProvider.get_history(...) but before makes sure that the query doesn't concern data from the future.

        See Also
        --------
        DataProvider.get_history
        """
        pass

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, Union[QFSeries, QFDataFrame]]:
        return self.data_provider.get_futures_chain_tickers(tickers, expiration_date_fields)

    @abstractmethod
    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                                 frequency: Frequency = None) -> Union[float, pd.Series]:
        """
        Gets the latest available price for given assets.

        Parameters
        -----------
        tickers: Ticker, Sequence[Ticker]
            tickers of the securities which prices should be downloaded
        frequency: Frequency
            frequency of the data

        Returns
        -------
        float, pandas.Series
            last_prices series where:
            - last_prices.name contains a date of current prices,
            - last_prices.index contains tickers
            - last_prices.data contains latest available prices for given tickers
        """
        pass

    def get_current_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                          frequency: Frequency = None) -> Union[float, pd.Series]:
        """
        Works just like get_last_available_price() but it can return NaNs if data is not available at the current
        moment.

        Parameters
        -----------
        tickers: Ticker, Sequence[Ticker]
            tickers of the securities which prices should be downloaded
        frequency: Frequency
            frequency of the data

        Returns
        -------
        float, pandas.Series
            current_prices series where:
            - current_prices.name contains a date of current prices,
            - current_prices.index contains tickers
            - current_prices.data contains latest available prices for given tickers
        """
        pass

    def get_current_bar(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None) \
            -> Union[pd.Series, pd.DataFrame]:
        """
        Gets the current bar(s) for given Ticker(s). If the bar is not available yet, None is returned.

        Parameters
        -----------
        tickers: Ticker, Sequence[Ticker]
            tickers of the securities which prices should be downloaded
        frequency: Frequency
            frequency of the data

        Returns
        -------
        pandas.Series, pandas.DataFrame
            current bar
        """
        pass

    @abstractmethod
    def _get_end_date_without_look_ahead(self, end_date=None):
        pass

    def supported_ticker_types(self):
        return self.data_provider.supported_ticker_types()


class _DataHandlerTimeHelper(object):
    """
    Helper class extracting from DataHandler all the logic connected with time,
    that is logic which makes sure that no data from the future is accessed in the backtest.
    """

    def __init__(self, timer: Timer):
        self.timer = timer

    def datetime_of_latest_market_event(self, event_class: Type[RegularTimeEvent]):
        time_of_event = event_class.trigger_time()

        now = self.timer.now()

        today_market_event = now + time_of_event
        yesterday_market_event = today_market_event - RelativeDelta(days=1)

        if now < today_market_event:  # event hasn't occurred today yet
            latest_available_market_event = yesterday_market_event
        else:  # event occurred today already
            latest_available_market_event = today_market_event

        return latest_available_market_event
