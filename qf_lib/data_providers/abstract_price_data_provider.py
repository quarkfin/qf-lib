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

from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Union, Sequence, Dict

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.helpers import normalize_data_array


class AbstractPriceDataProvider(DataProvider, metaclass=ABCMeta):
    """
    An interface for data providers containing historical data of stocks, indices, futures
    and other asset classes. This is a base class of any simple data provider (a data provider that is associated with
    single data base, for example: Quandl, Bloomberg, Yahoo.)
    """

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY) -> \
            Union[None, PricesSeries, PricesDataFrame, QFDataArray]:

        if end_date:
            end_date = end_date + RelativeDelta(second=0, microsecond=0)
        start_date = self._adjust_start_date(start_date, frequency)
        got_single_date = self._got_single_date(start_date, end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, Ticker)
        fields, got_single_field = convert_to_list(fields, PriceField)

        fields_str = self._map_field_to_str(tickers, fields)
        container = self.get_history(tickers, fields_str, start_date, end_date, frequency)

        str_to_field_dict = self.str_to_price_field_map(self._get_first_ticker(tickers))

        # Map the specific fields onto the fields given by the str_to_field_dict
        if isinstance(container, QFDataArray):
            container = container.assign_coords(fields=[str_to_field_dict[field_str] for field_str in container.fields.values])
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
    def price_field_to_str_map(self, ticker: Ticker = None) -> Dict[PriceField, str]:
        """
        Method has to be implemented in each data provider in order to be able to use get_price.
        Returns dictionary containing mapping between PriceField and corresponding string that has to be used by
        get_history method to get appropriate type of price series.

        Parameters
        -----------
        ticker: None, Ticker
            ticker is optional and might be uses by particular data providers to create appropriate dictionary

        Returns
        -------
        Dict[PriceField, str]
             mapping between PriceFields and corresponding strings
        """
        raise NotImplementedError()

    @abstractmethod
    def expiration_date_field_str_map(self, ticker: Ticker = None) -> Dict[ExpirationDateField, str]:
        """
        Method has to be implemented in each data provider in order to be able to use get_futures_chain_tickers.
        Returns dictionary containing mapping between ExpirationDateField and corresponding string that has to be used
        by get_futures_chain_tickers method.

        Parameters
        -----------
        ticker: None, Ticker
            ticker is optional and might be uses by particular data providers to create appropriate dictionary

        Returns
        -------
        Dict[ExpirationDateField, str]
             mapping between ExpirationDateField and corresponding strings
        """
        pass

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, QFDataFrame]:

        expiration_date_fields, got_single_expiration_date_field = convert_to_list(expiration_date_fields,
                                                                                   ExpirationDateField)
        mapping_dict = self.expiration_date_field_str_map()
        expiration_date_fields_str = [mapping_dict[field] for field in expiration_date_fields]
        exp_dates_dict = self._get_futures_chain_dict(tickers, expiration_date_fields_str)

        for future_ticker, exp_dates in exp_dates_dict.items():
            exp_dates = exp_dates.rename(columns=self.str_to_expiration_date_field_map())
            for ticker in exp_dates.index:
                ticker.security_type = future_ticker.security_type
                ticker.point_value = future_ticker.point_value
                ticker.set_name(future_ticker.name)
            if got_single_expiration_date_field:
                exp_dates = exp_dates.squeeze()
            exp_dates_dict[future_ticker] = exp_dates

        return exp_dates_dict

    @abstractmethod
    def _get_futures_chain_dict(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]]) -> Dict[FutureTicker, QFDataFrame]:
        """
        Returns a dictionary, which maps Tickers to QFSeries, consisting of the expiration dates of Future
        Contracts: Dict[FutureTicker, Union[QFSeries, QFDataFrame]]].

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            tickers for securities which should be retrieved
        expiration_date_fields: str, Sequence[str]
            expiration date fields of securities which should be retrieved. Specific for each data provider,
            the mapping between strings and corresponding ExpirationDateField enum values should be implemented as
            str_to_expiration_date_field_map function.
        """
        pass

    def str_to_expiration_date_field_map(self, ticker: Ticker = None) -> Dict[str, ExpirationDateField]:
        """
        Inverse of str_to_expiration_date_field_map.
        """
        field_str_dict = self.expiration_date_field_str_map(ticker)
        inv_dict = {v: k for k, v in field_str_dict.items()}
        return inv_dict

    def str_to_price_field_map(self, ticker: Ticker = None) -> Dict[str, PriceField]:
        """
        Inverse of price_field_to_str_map.
        """
        field_str_dict = self.price_field_to_str_map(ticker)
        inv_dict = {v: k for k, v in field_str_dict.items()}
        return inv_dict

    def _map_field_to_str(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[None, PriceField, Sequence[PriceField]]) \
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

    def _get_first_ticker(self, tickers):
        if self._is_single_ticker(tickers):
            ticker = tickers
        else:
            ticker = tickers[0]
        return ticker
