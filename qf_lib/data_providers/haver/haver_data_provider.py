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

import os
import threading
import warnings
from datetime import datetime
from typing import Union, Sequence, Dict, Optional

from pandas import PeriodIndex, DataFrame
from qf_lib.common.enums.expiration_date_field import ExpirationDateField

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import HaverTicker, Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.settings import Settings

try:
    import Haver

    is_haver_installed = True
except ImportError:
    is_haver_installed = False
    warnings.warn("No Haver installed. If you would like to use HaverDataProvider first install the Haver library.")


class HaverDataProvider(AbstractPriceDataProvider):
    """
    Constructs a new ``HaverDataProvider`` instance.

    Parameters
    ----------
    settings
        Settings object, which should contain path to the directory with the Haver database
    """
    get_lock = threading.Lock()

    def __init__(self, settings: Settings):
        self.db_location = settings.haver_path
        self.connected = False

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_history(self, tickers: Union[HaverTicker, Sequence[HaverTicker]], fields=None, start_date: datetime = None,
                    end_date: datetime = None, **kwargs) -> Union[QFSeries, QFDataFrame]:
        """ Gets historical fields for Haver tickers.

        Parameters
        -------------
        tickers: HaverTicker, Sequence[HaverTicker]
            Haver tickers, for which the prices should be returned
        fields
            should be equal to None as each ticker corresponds to one timeseries and there is no such thing as a field
            in the Haver DB
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used

        Returns
        ------------
        QFSeries, QFDataFrame
        """
        if fields is not None:
            self.logger.warning("Data field is provided but it will nor be used")

        self._connect_if_needed()
        HaverDataProvider.get_lock.acquire()

        try:
            if isinstance(tickers, HaverTicker):
                return self._get_single(tickers, start_date, end_date)
            else:
                result = QFDataFrame()
                # we should go one by one as making single large query will keep just common dates
                for ticker in tickers:
                    series = self._get_single(ticker, start_date, end_date)
                    result[ticker] = series
                return result
        finally:
            HaverDataProvider.get_lock.release()

    def supported_ticker_types(self):
        return {HaverTicker}

    def price_field_to_str_map(self, ticker: HaverTicker = None) -> Dict[PriceField, Optional[str]]:
        """
        Haver stores only end of day figures. Use PriceField.Close to obtain them
        """
        price_field_dict = {PriceField.Close: None}  # Field representation is none as Field is unused
        return price_field_dict

    @staticmethod
    def _get_single(haver_ticker, start_date: datetime, end_date) -> QFSeries:
        if start_date is not None:
            start_date = start_date.date()
        if end_date is not None:
            end_date = end_date.date()

        ticker_str = [haver_ticker.database_name + ':' + haver_ticker.ticker]
        raw_series = Haver.data(ticker_str, startdate=start_date, enddate=end_date)
        if isinstance(raw_series, DataFrame):
            if isinstance(raw_series.index, PeriodIndex):
                raw_series.index = raw_series.index.to_timestamp()
            result = QFSeries(raw_series.iloc[:, 0])
        else:
            result = QFSeries()

        result.name = haver_ticker.as_string()
        return result

    def connect(self):
        if is_haver_installed:
            if os.path.exists(self.db_location):
                Haver.path(self.db_location)
                self.connected = True
            else:
                self.logger.warning("Couldn't access Haver directory. Probably there is no access to the O: drive.")

    def _connect_if_needed(self):
        """
        Calling this function should be the first line in any method accessing the database
        It was introduced to make the use of the database lazy and connect only when used requests data
        """
        if not self.connected:
            self.connect()

        if not self.connected:
            raise ConnectionError("No Haver connection.")

    def _get_futures_chain_dict(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]]) -> Dict[FutureTicker, QFDataFrame]:
        raise NotImplementedError("Downloading Future Chain Tickers in HaverDataProvider is not supported yet")

    def expiration_date_field_str_map(self, ticker: Ticker = None) -> Dict[ExpirationDateField, str]:
        pass
