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
from itertools import groupby
from typing import Sequence, Union, Dict, Type

import pandas as pd

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import TICKERS
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.haver import HaverDataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.data_providers.bloomberg.bloomberg_data_provider import BloombergDataProvider


class GeneralPriceProvider(DataProvider):
    """
    The main class that should be used in order to access prices of financial instruments.
    """

    def __init__(self, bloomberg: BloombergDataProvider = None, quandl: QuandlDataProvider = None,
                 haver: HaverDataProvider = None):
        super().__init__()
        self._ticker_type_to_data_provider_dict = {}  # type: Dict[Type[Ticker], DataProvider]

        for provider in [bloomberg, quandl, haver]:
            if provider is not None:
                self._register_data_provider(provider)

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY) -> Union[None, PricesSeries, PricesDataFrame, QFDataArray]:
        """
        Implements the functionality of AbstractPriceDataProvider using duck-typing.

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
            data of lower dimensionality will be returned.
        """
        use_prices_types = True
        normalized_result = self._get_data_for_multiple_tickers(tickers, fields, start_date, end_date, frequency, use_prices_types)

        return normalized_result

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]], start_date: datetime,
            end_date: datetime = None, frequency: Frequency = Frequency.DAILY, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Implements the functionality of DataProvider using duck-typing.

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
            dimensionality will be returned.
        """
        use_prices_types = False
        normalized_result = self._get_data_for_multiple_tickers(tickers, fields, start_date, end_date, frequency,
                                                                use_prices_types)

        return normalized_result

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, Union[QFSeries, QFDataFrame]]:
        """
        Implements the functionality of DataProvider using duck-typing.

        Returns tickers of futures contracts, which belong to the same futures contract chain as the provided ticker
        (tickers), along with their expiration dates in form of a QFSeries.

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
            Contracts
        """
        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        results = {}

        def get_data_func(data_prov: DataProvider, tickers_for_single_data_provider) -> Dict[FutureTicker, QFSeries]:
            return data_prov.get_futures_chain_tickers(tickers_for_single_data_provider, ExpirationDateField.all_dates())

        for ticker_class, ticker_group in groupby(tickers, lambda t: type(t)):
            data_provider = self._identify_data_provider(ticker_class)
            partial_result = get_data_func(data_provider, list(ticker_group))
            if partial_result is not None:
                results.update(partial_result)

        return results

    def supported_ticker_types(self):
        return self._ticker_type_to_data_provider_dict.keys()

    def _get_data_for_multiple_tickers(self, tickers, fields, start_date, end_date, frequency, use_prices_types):
        if use_prices_types:
            type_of_field = PriceField

            def get_data_func(data_prov: DataProvider, tickers_for_single_data_provider):
                prices = data_prov.get_price(tickers_for_single_data_provider, fields, start_date, end_date,
                                             frequency)
                return prices
        else:
            type_of_field = str

            def get_data_func(data_prov: DataProvider, tickers_for_single_data_provider):
                prices = data_prov.get_history(tickers_for_single_data_provider, fields, start_date, end_date,
                                               frequency)
                return prices

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, type_of_field)
        got_single_date = self._got_single_date(start_date, end_date, frequency)
        partial_results = []

        for ticker_class, ticker_group in groupby(tickers, lambda t: type(t)):
            data_provider = self._identify_data_provider(ticker_class)
            partial_result = get_data_func(data_provider, list(ticker_group))
            if partial_result is not None:
                partial_results.append(partial_result)

        if not all(isinstance(partial_result, type(partial_results[0])) for partial_result in partial_results):
            raise ValueError('Not all partial result are the same type')

        if isinstance(partial_results[0], QFDataArray):
            result = QFDataArray.concat(partial_results, dim=TICKERS)
            result = normalize_data_array(
                result, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types)
        else:
            result = pd.concat(partial_results).squeeze(axis=1)

        return result

    def _register_data_provider(self, price_provider: DataProvider):
        for ticker_class in price_provider.supported_ticker_types():
            self._ticker_type_to_data_provider_dict[ticker_class] = price_provider

    def _identify_data_provider(self, ticker_class: Type[Ticker]) -> DataProvider:
        """
        Defines the association between ticker type and data provider.
        """
        data_provider = self._ticker_type_to_data_provider_dict.get(ticker_class, None)
        if data_provider is None:
            raise LookupError(
                "Unknown ticker type: {}. No appropriate data provider found".format(str(ticker_class)))

        return data_provider
