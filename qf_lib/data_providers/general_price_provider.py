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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dimension_names import TICKERS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg.bloomberg_data_provider import BloombergDataProvider
from qf_lib.data_providers.cryptocurrency.cryptocurrency_data_provider import CryptoCurrencyDataProvider
from qf_lib.data_providers.haver import HaverDataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.data_providers.price_data_provider import DataProvider
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider


class GeneralPriceProvider(DataProvider):
    """
    The main class that should be used in order to access prices of financial instruments.
    """

    def __init__(self, bloomberg: BloombergDataProvider = None, quandl: QuandlDataProvider = None,
                 haver: HaverDataProvider = None, cryptocurrency: CryptoCurrencyDataProvider = None):
        self._ticker_type_to_data_provider_dict = {}  # type: Dict[Type[Ticker], DataProvider]

        for provider in [bloomberg, quandl, haver, cryptocurrency]:
            if provider is not None:
                self._register_data_provider(provider)

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY) -> Union[None, PricesSeries, PricesDataFrame, QFDataArray]:
        """"
        Implements the functionality of AbstractPriceDataProvider using duck-typing.
        """
        use_prices_types = True
        normalized_result = self._get_data_for_multiple_tickers(tickers, fields, start_date, end_date, frequency, use_prices_types)

        return normalized_result

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]], start_date: datetime,
            end_date: datetime = None, frequency: Frequency = Frequency.DAILY, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """"
        Implements the functionality of DataProvider using duck-typing.
        """
        use_prices_types = False
        normalized_result = self._get_data_for_multiple_tickers(tickers, fields, start_date, end_date, frequency,
                                                                use_prices_types)

        return normalized_result

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
        got_single_date = start_date is not None and (
            (start_date == end_date) if frequency <= Frequency.DAILY else False
        )
        partial_results = []

        for ticker_class, ticker_group in groupby(tickers, lambda t: type(t)):
            data_provider = self._identify_data_provider(ticker_class)

            partial_result = get_data_func(data_provider, list(ticker_group))
            if partial_result is not None:
                partial_results.append(partial_result)

        result = QFDataArray.concat(partial_results, dim=TICKERS)
        normalized_result = normalize_data_array(
            result, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types)
        return normalized_result

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
