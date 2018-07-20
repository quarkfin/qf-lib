from datetime import datetime
from itertools import groupby
from typing import Sequence, Union, Dict, Type

import pandas as pd
from pandas import Panel, concat

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.bloomberg.bloomberg_data_provider import BloombergDataProvider
from qf_lib.data_providers.cryptocurrency.cryptocurrency_data_provider import CryptoCurrencyDataProvider
from qf_lib.data_providers.haver import HaverDataProvider
from qf_lib.data_providers.price_data_provider import DataProvider
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider


class GeneralPriceProvider(DataProvider):
    """"
    The main class that should be used in order to access prices of financial instruments.
    """

    def __init__(self, bloomberg: BloombergDataProvider=None, quandl: QuandlDataProvider=None,
                 haver: HaverDataProvider=None, cryptocurrency: CryptoCurrencyDataProvider=None):
        self._ticker_type_to_data_provider_dict = {}  # type: Dict[Type[Ticker], DataProvider]

        for provider in [bloomberg, quandl, haver, cryptocurrency]:
            if provider is not None:
                self._register_data_provider(provider)

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime=None) \
            -> Union[None, PricesSeries, PricesDataFrame, Panel]:
        """"
        Implements the functionality of AbstractPriceDataProvider using duck-typing.
        """
        if isinstance(tickers, Ticker):  # we have a single ticker
            data_provider = self._identify_data_provider(type(tickers))
            return data_provider.get_price(tickers, fields, start_date, end_date)
        else:  # we have multiple tickers that might come from different data providers
            return self._get_price_multiple_tickers(end_date, fields, start_date, tickers)

    def supported_ticker_types(self):
        return self._ticker_type_to_data_provider_dict.keys()

    def get_history(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, **kwargs) \
            -> Union[QFSeries, QFDataFrame, pd.Panel]:
        """"
        Implements the functionality of AbstractDataProvider using duck-typing.
        """
        if isinstance(tickers, Ticker):  # we have a single ticker
            data_provider = self._identify_data_provider(type(tickers))
            return data_provider.get_history(tickers, fields, start_date, end_date)
        else:  # we have multiple tickers that might come from different data providers
            return self._get_history_multiple_tickers(end_date, fields, start_date, tickers)

    def _register_data_provider(self, price_provider: DataProvider):
        for ticker_class in price_provider.supported_ticker_types():
            self._ticker_type_to_data_provider_dict[ticker_class] = price_provider

    def _get_price_multiple_tickers(self, end_date, fields, start_date, tickers):
        is_single_field = isinstance(fields, PriceField)
        container = self._get_empty_container(is_single_field)
        for ticker_class, ticker_group in groupby(tickers, lambda t: type(t)):
            data_provider = self._identify_data_provider(ticker_class)

            # quandl can only handle one query per quandl database. We split tickers if needed.
            if isinstance(data_provider, QuandlDataProvider):
                partial_result = self._get_empty_container(is_single_field)
                for quandl_db_name, quandl_ticker_group in groupby(ticker_group, lambda t: t.database_name):
                    single_db_result = data_provider.get_price(
                        list(quandl_ticker_group), fields, start_date, end_date)
                    partial_result = self._append_to_container(
                        partial_result, single_db_result)
            else:
                partial_result = data_provider.get_price(
                    list(ticker_group), fields, start_date, end_date)

            if partial_result is not None:
                container = self._append_to_container(
                    container, partial_result)
        return container

    def _get_history_multiple_tickers(self, end_date, fields, start_date, tickers):
        is_single_field = isinstance(fields, str)
        container = self._get_empty_general_container(is_single_field)
        for ticker_class, ticker_group in groupby(tickers, lambda t: type(t)):
            data_provider = self._identify_data_provider(ticker_class)

            # quandl can only handle one query per quandl database. We split tickers if needed.
            if isinstance(data_provider, QuandlDataProvider):
                partial_result = self._get_empty_general_container(is_single_field)
                for quandl_db_name, quandl_ticker_group in groupby(ticker_group, lambda t: t.database_name):
                    single_db_result = data_provider.get_history(
                        list(quandl_ticker_group), fields, start_date, end_date)
                    partial_result = concat([partial_result, single_db_result], axis=1, join='outer')
            else:
                partial_result = data_provider.get_history(list(ticker_group), fields, start_date, end_date)

            if partial_result is not None:
                container = concat([container, partial_result], axis=1, join='outer')
        return container

    def _identify_data_provider(self, ticker_class: Type[Ticker]) -> DataProvider:
        """
        Defines the association between ticker type and data provider.
        """
        data_provider = self._ticker_type_to_data_provider_dict.get(ticker_class, None)
        if data_provider is None:
            raise LookupError(
                "Unknown ticker type: {}. No appropriate data provider found".format(str(ticker_class))
            )

        return data_provider

    @staticmethod
    def _get_empty_container(is_single_field) -> Union[PricesDataFrame, Panel]:
        if is_single_field:
            return PricesDataFrame()
        else:
            return Panel()

    @staticmethod
    def _get_empty_general_container(is_single_field) -> Union[QFDataFrame, Panel]:
        if is_single_field:
            return QFDataFrame()
        else:
            return Panel()

    @staticmethod
    def _append_to_container(container: Union[PricesDataFrame, Panel], partial_result: Union[PricesDataFrame, Panel])\
            -> Union[PricesDataFrame, Panel]:
        return concat([container, partial_result], axis=1, join='outer')
