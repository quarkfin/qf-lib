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
from typing import Union, Sequence, Optional, Dict

from pandas import date_range

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider


class DataHandler(DataProvider):
    """
    DataHandler is a wrapper which can be used with any AbstractPriceDataProvider in both live and backtest
    environment. It makes sure that data "from the future" is not passed into components in the backtest environment.

    DataHandler should be used by all the Backtester's components (even in the live trading setup).

    The goal of a DataHandler is to provide backtester's components with financial data. It makes sure that
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
        super().__init__()
        self.data_provider = data_provider

        self._check_frequency(data_provider.frequency)
        self.default_frequency = data_provider.frequency  # type: Frequency

        self.timer = timer
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
        self.default_frequency = frequency

        self.data_provider = PrefetchingDataProvider(self.data_provider, tickers, fields, start_date, end_date,
                                                     frequency)
        self.is_optimised = True

    def historical_price(self, tickers: Union[Ticker, Sequence[Ticker]],
                         fields: Union[PriceField, Sequence[PriceField]],
                         nr_of_bars: int, end_date: Optional[datetime] = None, frequency: Frequency = None) -> \
            Union[PricesSeries, PricesDataFrame, QFDataArray]:

        frequency = frequency or self.default_frequency
        end_date = self._get_end_date_without_look_ahead(end_date, frequency)
        return self.data_provider.historical_price(tickers, fields, nr_of_bars, end_date, frequency)

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = None) -> \
            Union[PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Runs DataProvider.get_price(...) but before makes sure that the query doesn't concern data from
        the future. It always returns the fully available bars (e.g. it will return a full bar for a day only after
        the market close).

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
        """
        frequency = frequency or self.default_frequency
        assert frequency is not None, "Frequency cannot be equal to None"

        start_date = self._adjust_start_date(start_date, frequency)
        end_date = end_date or self.timer.now()
        got_single_date = self._got_single_date(start_date, end_date, frequency)

        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_date, frequency)
        got_single_date_without_look_ahead = self._got_single_date(start_date, end_date_without_look_ahead, frequency)

        if start_date > end_date_without_look_ahead:
            prices_data = self._empty_container(tickers, fields, start_date, end_date, frequency)
        elif got_single_date != got_single_date_without_look_ahead:
            prices_data = self.data_provider.get_price(tickers, fields, start_date,
                                                       end_date_without_look_ahead + frequency.time_delta(), frequency)
            prices_data = prices_data.loc[start_date:end_date_without_look_ahead]
        else:
            prices_data = self.data_provider.get_price(tickers, fields, start_date, end_date_without_look_ahead,
                                                       frequency)

        return prices_data

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = None, **kwargs) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Runs DataProvider.get_history(...) but before makes sure that the query doesn't concern data from the future.

        It accesses the latest fully available bar as of "today", that is: if a bar wasn't closed for today yet,
        then all the PriceFields (e.g. OPEN) will concern data from yesterday.

        See Also
        --------
        DataProvider.get_history
        """
        frequency = frequency or self.default_frequency
        assert frequency is not None, "Frequency cannot be equal to None"

        start_date = self._adjust_start_date(start_date, frequency)
        single_date = self._got_single_date(start_date, end_date, frequency)
        end_date_without_look_ahead = self._get_end_date_without_look_ahead(end_date, frequency)

        if start_date > end_date_without_look_ahead:
            data = self._empty_container(tickers, fields, start_date, end_date, frequency)
        elif start_date.date() == end_date_without_look_ahead.date() and not single_date:
            data = self.data_provider.get_history(tickers, fields, start_date,
                                                  end_date_without_look_ahead + frequency.time_delta(), frequency)
            data = data.loc[start_date:end_date_without_look_ahead]
        else:
            data = self.data_provider.get_history(tickers, fields, start_date, end_date_without_look_ahead,
                                                  frequency)

        return data

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, Union[QFSeries, QFDataFrame]]:
        return self.data_provider.get_futures_chain_tickers(tickers, expiration_date_fields)

    def supported_ticker_types(self):
        return self.data_provider.supported_ticker_types()

    @abstractmethod
    def get_last_available_price(self, tickers: Union[Ticker, Sequence[Ticker]], frequency: Frequency = None,
                                 end_time: Optional[datetime] = None) -> Union[float, QFSeries]:
        pass

    @abstractmethod
    def _get_end_date_without_look_ahead(self, end_date: datetime, frequency: Frequency):
        pass

    @abstractmethod
    def _check_frequency(self, frequency):
        """ Verify if the provided frequency is compliant with the type of Data Handler used. """
        pass

    def _empty_container(self, tickers, fields, start_date, end_date, frequency):
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, (str, PriceField))
        got_single_date = self._got_single_date(start_date, end_date, frequency)

        dates = date_range(start_date, end_date, freq=frequency.to_pandas_freq())
        data_array = QFDataArray.create(dates, tickers, fields, data=None)
        return normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker,
                                    got_single_field, True)
