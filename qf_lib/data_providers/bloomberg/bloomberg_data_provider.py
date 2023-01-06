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
import warnings

import pandas as pd
from datetime import datetime
from typing import Union, Sequence, Dict, List, Optional

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider
from qf_lib.settings import Settings

try:
    import blpapi

    from qf_lib.data_providers.bloomberg.futures_data_provider import FuturesDataProvider
    from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider
    from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider
    from qf_lib.data_providers.bloomberg.tabular_data_provider import TabularDataProvider
    from qf_lib.data_providers.bloomberg.exceptions import BloombergError
    from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI
    from qf_lib.data_providers.bloomberg.helpers import convert_to_bloomberg_date

    is_blpapi_installed = True
except ImportError:
    is_blpapi_installed = False
    warnings.warn("No Bloomberg API installed. If you would like to use BloombergDataProvider first install the blpapi"
                  " library")


class BloombergDataProvider(AbstractPriceDataProvider, TickersUniverseProvider):
    """
    Data Provider which provides financial data from Bloomberg.
    """

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

        self.host = settings.bloomberg.host
        self.port = settings.bloomberg.port
        self.logger = qf_logger.getChild(self.__class__.__name__)

        if is_blpapi_installed:
            session_options = blpapi.SessionOptions()
            session_options.setServerHost(self.host)
            session_options.setServerPort(self.port)
            session_options.setAutoRestartOnDisconnection(True)
            self.session = blpapi.Session(session_options)

            self._historical_data_provider = HistoricalDataProvider(self.session)
            self._reference_data_provider = ReferenceDataProvider(self.session)
            self._tabular_data_provider = TabularDataProvider(self.session)
            self._futures_data_provider = FuturesDataProvider(self.session)
        else:
            self.session = None
            self._historical_data_provider = None
            self._reference_data_provider = None
            self._tabular_data_provider = None
            self._futures_data_provider = None

            self.logger.warning("Couldn't import the Bloomberg API. Check if the necessary dependencies are installed.")

        self.connected = False

    def connect(self):
        """
        Connects to Bloomberg data service and holds a connection.
        Connecting might take about 10-15 seconds
        """
        self.connected = False
        if not is_blpapi_installed:
            self.logger.error("Couldn't import the Bloomberg API. Check if the necessary dependencies are installed.")
            return

        if not self.session.start():
            self.logger.error("Failed to start session with host: " + str(self.host) + " on port: " + str(self.port))
            return

        if not self.session.openService(REF_DATA_SERVICE_URI):
            self.logger.error("Failed to open service: " + REF_DATA_SERVICE_URI)
            return

        self.connected = True

    def _get_futures_chain_dict(self, tickers: Union[BloombergFutureTicker, Sequence[BloombergFutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]]) -> Dict[BloombergFutureTicker, QFDataFrame]:
        """
        Returns tickers of futures contracts, which belong to the same futures contract chain as the provided ticker
        (tickers), along with their expiration dates.

        Parameters
        ----------
        tickers: BloombergFutureTicker, Sequence[BloombergFutureTicker]
            future tickers for which future chains should be retrieved
        expiration_date_fields: ExpirationDateField, Sequence[ExpirationDateField]
            field that should be downloaded as the expiration date field

        Returns
        -------
        Dict[BloombergFutureTicker, QFDataFrame]
            Dictionary mapping each BloombergFutureTicker to a QFDataFrame, containing specific future
            contracts tickers (BloombergTickers), indexed by these tickers

        Raises
        -------
        BloombergError
            When couldn't get the data from Bloomberg Service
        """
        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergFutureTicker)
        expiration_date_fields, _ = convert_to_list(expiration_date_fields, str)

        # Create a dictionary, which is mapping BloombergFutureTickers to lists of tickers related to specific future
        # contracts belonging to the chain, e.g. it will map Cotton Bloomberg future ticker into:
        # [BloombergTicker("CTH7 Comdty"), BloombergTicker("CTK7 Comdty"), BloombergTicker("CTN7 Comdty"),
        # BloombergTicker("CTV7 Comdty"), BloombergTicker("CTZ7 Comdty") ... ]
        future_ticker_to_chain_tickers_list: Dict[BloombergFutureTicker, List[BloombergTicker]] = \
            self._futures_data_provider.get_list_of_tickers_in_the_future_chain(tickers)
        all_specific_tickers = [ticker for specific_tickers_list in future_ticker_to_chain_tickers_list.values()
                                for ticker in specific_tickers_list]
        futures_expiration_dates = self.get_current_values(all_specific_tickers, expiration_date_fields).dropna(how="all")

        def specific_futures_index(future_ticker) -> pd.Index:
            """
            Returns an Index of specific tickers for the given future ticker, which appeared in the futures
            expiration dates dataframe / series.
            """
            specific_tickers_list = future_ticker_to_chain_tickers_list[future_ticker]
            return futures_expiration_dates.index.intersection(specific_tickers_list)

        ticker_to_future_expiration_dates = {
            future_ticker: futures_expiration_dates.loc[specific_futures_index(future_ticker)]
            for future_ticker in tickers
        }

        return ticker_to_future_expiration_dates

    def get_current_values(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]],
                           fields: Union[str, Sequence[str]], override_name: str = None, override_value: str = None
                           ) -> Union[None, float, str, QFSeries, QFDataFrame]:
        """
        Gets the current values of fields for given tickers.

        Parameters
        ----------
        tickers: BloombergTicker, Sequence[BloombergTicker]
            tickers for securities which should be retrieved
        fields: str, Sequence[str]
            fields of securities which should be retrieved

        Returns
        -------
        QFDataFrame/QFSeries
            Either QFDataFrame with 2 dimensions: ticker, field or QFSeries with 1 dimensions: ticker of field
            (depending if many tickers or fields was provided) is returned.

        Raises
        -------
        BloombergError
            When couldn't get the data from Bloomberg Service
        """
        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        data_frame = self._reference_data_provider.get(tickers, fields, override_name, override_value)

        # to keep the order of tickers and fields we reindex the data frame
        data_frame = data_frame.reindex(index=tickers, columns=fields)

        # squeeze unused dimensions
        tickers_indices = 0 if got_single_ticker else slice(None)
        fields_indices = 0 if got_single_field else slice(None)
        squeezed_result = data_frame.iloc[tickers_indices, fields_indices]

        casted_result = cast_dataframe_to_proper_type(squeezed_result) if tickers_indices != 0 or fields_indices != 0 \
            else squeezed_result

        return casted_result

    def get_history(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY,
                    currency: str = None, override_name: str = None, override_value: str = None) \
            -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical data from Bloomberg from the (start_date - end_date) time range. In case of frequency, which is
        higher than daily frequency (intraday data), the data is indexed by the start_date. E.g. Time range: 8:00 - 8:01,
        frequency: 1 minute - indexed with the 8:00 timestamp

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
        currency: str
        override_name: str
        override_value: str

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
        if fields is None:
            raise ValueError("Fields being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        end_date = end_date or datetime.now()
        end_date = end_date + RelativeDelta(second=0, microsecond=0)
        start_date = self._adjust_start_date(start_date, frequency)

        got_single_date = self._got_single_date(start_date, end_date, frequency)
        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        def current_ticker(t: BloombergTicker):
            return t.get_current_specific_ticker() if isinstance(t, BloombergFutureTicker) else t

        tickers_mapping = {current_ticker(t): t for t in tickers}
        data_array = self._historical_data_provider.get(
            tickers, fields, start_date, end_date, frequency, currency, override_name, override_value)
        data_array = data_array.assign_coords(tickers=[tickers_mapping.get(t, t) for t in data_array.tickers.values])

        normalized_result = normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field)

        return normalized_result

    def supported_ticker_types(self):
        return {BloombergTicker, BloombergFutureTicker}

    def expiration_date_field_str_map(self, ticker: BloombergTicker = None) -> Dict[ExpirationDateField, str]:
        expiration_date_field_dict = {
            ExpirationDateField.FirstNotice: "FUT_NOTICE_FIRST",
            ExpirationDateField.LastTradeableDate: "LAST_TRADEABLE_DT"
        }
        return expiration_date_field_dict

    def price_field_to_str_map(self, ticker: BloombergTicker = None) -> Dict[PriceField, str]:
        price_field_dict = {
            PriceField.Open: 'PX_OPEN',
            PriceField.High: 'PX_HIGH',
            PriceField.Low: 'PX_LOW',
            PriceField.Close: 'PX_LAST',
            PriceField.Volume: 'PX_VOLUME'
        }
        return price_field_dict

    def get_tickers_universe(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None) -> List[BloombergTicker]:
        date = date or datetime.now()
        field = 'INDX_MWEIGHT_HIST'
        ticker_data = self.get_tabular_data(universe_ticker, field, override_names="END_DT",
                                            override_values=convert_to_bloomberg_date(date))
        return [BloombergTicker(fields['Index Member'] + " Equity", SecurityType.STOCK, 1) for fields in ticker_data]

    def get_unique_tickers(self, universe_ticker: Ticker) -> List[Ticker]:
        raise ValueError("BloombergDataProvider does not provide historical tickers_universe data")

    def get_tabular_data(self, ticker: BloombergTicker, field: str,
                         override_names: Optional[Union[str, Sequence[str]]] = None,
                         override_values: Optional[Union[str, Sequence[str]]] = None) -> List:
        """
        Provides current tabular data from Bloomberg.

        Was tested on 'INDX_MEMBERS' and 'MERGERS_AND_ACQUISITIONS' requests. There is no guarantee that
        all other request will be handled, as returned data structures might vary.

        Parameters
        -----------
        ticker: BloombergTicker
            ticker for security that should be retrieved
        field: str
            field of security that should be retrieved
        override_names: str
        override_values: str

        Returns
        -------
        List
            tabular data for the given ticker and field
        """
        if field is None:
            raise ValueError("Field being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        if override_names is not None:
            override_names, _ = convert_to_list(override_names, str)
        if override_values is not None:
            override_values, _ = convert_to_list(override_values, str)

        tickers, got_single_ticker = convert_to_list(ticker, BloombergTicker)
        fields, got_single_field = convert_to_list(field, (PriceField, str))

        tickers_str = [t.as_string() for t in tickers]
        result = self._tabular_data_provider.get(tickers_str, fields, override_names, override_values)

        return result

    def _connect_if_needed(self):
        if not self.connected:
            self.connect()

    def _assert_is_connected(self):
        if not self.connected:
            raise BloombergError("Connection to Bloomberg was not successful.")
