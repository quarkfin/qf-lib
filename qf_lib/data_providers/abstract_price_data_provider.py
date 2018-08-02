from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Union, Sequence, Dict

import pandas as pd

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.price_data_provider import DataProvider


class AbstractPriceDataProvider(DataProvider, metaclass=ABCMeta):
    """
    An interface for data providers containing historical data of stocks, indices, futures
    and other asset classes. This is a base class of any simple data provider (a data provider that is associated with
    single data base, for example: Quandl, Bloomberg, Yahoo.)
    """

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime=None) \
            -> Union[None, PricesSeries, PricesDataFrame, pd.Panel]:
        if start_date == end_date:
            raise NotImplementedError("Single date queries are not supported yet")

        fields_str = self._map_field_to_str(tickers, fields)
        container = self.get_history(tickers, fields_str, start_date, end_date)

        # Convert to PriceSeries / PriceDataFrame and replace the string index with PriceField index
        if self._is_single_price_field(fields):
            if self._is_single_ticker(tickers):
                container = cast_series(container, PricesSeries)
            else:
                container = cast_dataframe(container, PricesDataFrame)
        else:
            str_to_field_dict = self.str_to_price_field_map(self._get_first_ticker(tickers))

            if self._is_single_ticker(tickers):
                # Many fields and single ticker - replace columns in PricesDataFrame
                container = cast_dataframe(container, PricesDataFrame)
                renaming_dict = {field_str: str_to_field_dict[field_str] for field_str in container.columns}
                container.rename(columns=renaming_dict, inplace=True)
            else:
                # Many tickers and many fields - replace minor axis in Panel
                price_fields = [str_to_field_dict[field_str] for field_str in container['fields'].values]
                container['fields'] = price_fields

        return container

    @abstractmethod
    def price_field_to_str_map(self, ticker: Ticker=None) -> Dict[PriceField, str]:
        """"
        Method has to be implemented in each data provider in order to be able to use get_price.
        Returns dictionary containing mapping between PriceField and corresponding string that has to be used by
        get_history method to get appropriate type of price series.

        Ticker is optional and might be use by particular data providers to create appropriate dictionary
        """

    def str_to_price_field_map(self, ticker: Ticker=None) -> Dict[str, PriceField]:
        """"
        Inverse of price_field_to_str_map.
        """
        field_str_dict = self.price_field_to_str_map(ticker)
        inv_dict = {v: k for k, v in field_str_dict.items()}
        return inv_dict

    def _map_field_to_str(self, tickers: Union[Ticker, Sequence[Ticker]],
                          fields: Union[None, PriceField, Sequence[PriceField]]) -> Union[None, str, Sequence[str]]:
        """"
        The method maps enum to sting that is recognised by the specific database.

        Parameters
        ----------
        fields
            fields of securities which should be retrieved

        Returns
        -------
        String representation of the field or fields that corresponds the API provided by a specific data provider
        Depending on the input it returns:
            None -> None
            PriceField -> str
            Sequence[PriceField] -> List[str]
        """
        if fields is None:
            return None

        field_str_dict = self.price_field_to_str_map(self._get_first_ticker(tickers))

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

    @staticmethod
    def _is_single_ticker(value):
        if isinstance(value, Ticker):
            return True

        return False

    @staticmethod
    def _is_single_date(start_date, end_date):
        return start_date is not None and (start_date == end_date)

    def _get_first_ticker(self, tickers):
        if self._is_single_ticker(tickers):
            ticker = tickers
        else:
            ticker = tickers[0]
        return ticker
