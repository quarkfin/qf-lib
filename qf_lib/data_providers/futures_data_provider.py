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

from abc import ABCMeta, abstractmethod
from typing import Union, Sequence, Dict

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker


class FuturesDataProvider(metaclass=ABCMeta):
    """
    An interface for providers of futures' data.
    """

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
        Dict[FutureTicker, QFDataFrame]
            Returns a dictionary, which maps Tickers to QFDataFrame, consisting of the expiration dates of Future
            Contracts: Dict[FutureTicker, QFDataFrame]]. The QFDataFrames contain the
            specific Tickers, which belong to the corresponding futures family, same as the FutureTicker, and are
            indexed by the expiration dates of the specific future contracts.
        """
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
            exp_dates_dict[future_ticker] = exp_dates

        return exp_dates_dict

    def str_to_expiration_date_field_map(self, ticker: Ticker = None) -> Dict[str, ExpirationDateField]:
        """
        Inverse of str_to_expiration_date_field_map.
        """
        field_str_dict = self.expiration_date_field_str_map(ticker)
        return {v: k for k, v in field_str_dict.items()}

    @abstractmethod
    def _get_futures_chain_dict(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]]) -> Dict[FutureTicker, QFDataFrame]:
        """
        Returns a dictionary, which maps Tickers to QFDataFrame, consisting of the expiration date(s) of Future
        Contracts: Dict[FutureTicker, QFDataFrame]]. The frame is indexed by the specific
        tickers belonging to the futures family.

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
