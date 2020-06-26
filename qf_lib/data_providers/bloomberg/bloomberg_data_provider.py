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
import pandas as pd
from datetime import datetime
from typing import Union, Sequence, Dict, List

import blpapi
from qf_lib.common.enums.expiration_date_field import ExpirationDateField

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker, tickers_as_strings
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg.futures_data_provider import FuturesDataProvider
from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider
from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider
from qf_lib.data_providers.bloomberg.tabular_data_provider import TabularDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider
from qf_lib.settings import Settings


class BloombergDataProvider(AbstractPriceDataProvider, TickersUniverseProvider):
    """
    Data Provider which provides financial data from Bloomberg.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        session_options = blpapi.SessionOptions()
        self.host = settings.bloomberg.host
        self.port = settings.bloomberg.port

        session_options.setServerHost(self.host)
        session_options.setServerPort(self.port)
        session_options.setAutoRestartOnDisconnection(True)
        self.session = blpapi.Session(session_options)

        self._historical_data_provider = HistoricalDataProvider(self.session)
        self._reference_data_provider = ReferenceDataProvider(self.session)
        self._tabular_data_provider = TabularDataProvider(self.session)
        self._futures_data_provider = FuturesDataProvider(self.session)
        self.connected = False
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def connect(self):
        """
        Connects to Bloomberg data service and holds a connection.
        Connecting might take about 10-15 seconds
        """
        self.connected = False
        if not self.session.start():
            self.logger.warning("Failed to start session with host: " + str(self.host) + " on port: " + str(self.port))
            return

        if not self.session.openService(REF_DATA_SERVICE_URI):
            self.logger.warning("Failed to open service: " + REF_DATA_SERVICE_URI)
            return

        self.connected = True

    def get_futures_chain_tickers(self, tickers: Union[BloombergFutureTicker, Sequence[BloombergFutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[BloombergFutureTicker, Union[QFSeries, QFDataFrame]]:
        """
        Returns tickers of futures contracts, which belong to the same futures contract chain as the provided ticker
        (tickers), along with their expiration dates.

        Parameters
        ----------
        tickers
            future tickers for which future chains should be retrieved
        expiration_date_fields
            field that should be downloaded as the expiration date field
        Returns
        -------
        Dict[BloombergFutureTicker, Union[QFSeries, QFDataFrame]]
            Dictionary mapping each BloombergFutureTicker to a QFSeries or QFDataFrame, containing specific future
            contracts tickers (BloombergTickers), indexed by these tickers
        Raises
        -------
        BloombergError
            When couldn't get the data from Bloomberg Service
        """
        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergFutureTicker)
        expiration_date_fields, got_single_expiration_date_field = convert_to_list(expiration_date_fields,
                                                                                   ExpirationDateField)

        # Create a dictionary, which is mapping BloombergFutureTickers to lists of tickers related to specific future
        # contracts belonging to the chain, e.g. it will map Cotton Bloomberg future ticker into:
        # [BloombergTicker("CTH7 Comdty"), BloombergTicker("CTK7 Comdty"), BloombergTicker("CTN7 Comdty"),
        # BloombergTicker("CTV7 Comdty"), BloombergTicker("CTZ7 Comdty") ... ]
        future_ticker_to_chain_tickers_list = self._futures_data_provider.get_list_of_tickers_in_the_future_chain(
            tickers)  # type: Dict[BloombergFutureTicker, List[BloombergTicker]]

        def get_futures_expiration_dates(specific_tickers: Union[BloombergTicker, Sequence[BloombergTicker]]) -> \
                Union[QFSeries, QFDataFrame]:
            """
            For a ticker (tickers) it returns a QFSeries or QFDataFrame consisting of the expiration dates fields of
            Future Contracts, that are defined by the given tickers.

            Parameters
            ----------
            specific_tickers
                tickers for which the expiration dates of future contracts should be retrieved
            Returns
            -------
            QFSeries, QFDataFrame
                Container containing all the dates, indexed by tickers
            """

            # Download the expiration dates for each of the future contracts
            mapping_dict = self.expiration_date_field_str_map()
            expiration_date_fields_str = [mapping_dict[field] for field in expiration_date_fields]
            exp_dates = self.get_current_values(specific_tickers, expiration_date_fields_str)  # type: Union[QFSeries, QFDataFrame]

            # Drop these futures, for which no expiration date was found and cast all string dates into datetime
            exp_dates = exp_dates.dropna(how="all")
            exp_dates = exp_dates.astype('datetime64[ns]')
            exp_dates = exp_dates.rename(columns=self.str_to_expiration_date_field_map())

            return exp_dates

        all_specific_tickers = [ticker for specific_tickers_list in future_ticker_to_chain_tickers_list.values()
                                for ticker in specific_tickers_list]
        futures_expiration_dates = get_futures_expiration_dates(all_specific_tickers)

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

    def get_current_values(
            self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]]) \
            -> Union[None, float, QFSeries, QFDataFrame]:
        """
        Gets the current values of fields for given tickers.

        Parameters
        ----------
        tickers
            tickers for securities which should be retrieved
        fields
            fields of securities which should be retrieved

        Returns
        -------
        QFDataFrame/QFSeries
            QFDataFrame  with 2 dimensions: ticker, field
            QFSeries     with 1 dimensions: ticker of field (depending if many tickers or fields was provided)

        Raises
        -------
        BloombergError
            When couldn't get the data from Bloomberg Service
        """
        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        tickers_str = tickers_as_strings(tickers)

        data_frame = self._reference_data_provider.get(tickers_str, fields)

        # to keep the order of tickers and fields we reindex the data frame
        data_frame = data_frame.reindex(index=tickers, columns=fields)

        # squeeze unused dimensions
        tickers_indices = 0 if got_single_ticker else slice(None)
        fields_indices = 0 if got_single_field else slice(None)
        squeezed_result = data_frame.iloc[tickers_indices, fields_indices]

        casted_result = cast_dataframe_to_proper_type(squeezed_result)

        return casted_result

    def get_history(
            self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, frequency: Frequency = Frequency.DAILY,
            currency: str = None,
            override_name: str = None, override_value: str = None) \
            -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical data from Bloomberg from the (start_date - end_date) time range. In case of frequency, which is
        higher than daily frequency (intraday data), the data is indexed by the start_date.
        E.g. Time range: 8:00 - 8:01, frequency: 1 minute - indexed with the 8:00 timestamp
        """
        if fields is None:
            raise ValueError("Fields being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        if end_date is None:
            end_date = datetime.now()

        got_single_date = start_date is not None and (
            (start_date == end_date) if frequency <= Frequency.DAILY else False
        )

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        tickers_mapping = {BloombergTicker.from_string(t.as_string()): t for t in tickers}
        tickers_str = tickers_as_strings(tickers)

        data_array = self._historical_data_provider.get(
            tickers_str, fields, start_date, end_date, frequency, currency, override_name, override_value)

        # Map each of the tickers in data array with corresponding ticker from tickers_mapping dictionary
        def _map_ticker(ticker):
            try:
                return tickers_mapping[ticker]
            except KeyError:
                return ticker

        data_array.tickers.values = [_map_ticker(t) for t in data_array.tickers.values]

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

    def get_tickers_universe(self, universe_ticker: BloombergTicker, date: datetime = None) -> List[BloombergTicker]:
        if date and date.date() != datetime.today().date():
            raise ValueError("BloombergDataProvider does not provide historical tickers_universe data")
        field = 'INDX_MEMBERS'
        ticker_data = self.get_tabular_data(universe_ticker, field)
        tickers = [BloombergTicker(fields['Member Ticker and Exchange Code'] + " Equity") for fields in ticker_data]
        return tickers

    def get_tabular_data(self, ticker: BloombergTicker, field: str) -> List:
        """
        Provides current tabular data from Bloomberg.

        Was tested on 'INDX_MEMBERS' and 'MERGERS_AND_ACQUISITIONS' requests. There is no guarantee that
        all other request will be handled, as returned data structures might vary.
        """
        if field is None:
            raise ValueError("Field being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(ticker, BloombergTicker)
        fields, got_single_field = convert_to_list(field, (PriceField, str))

        tickers_str = tickers_as_strings(tickers)
        result = self._tabular_data_provider.get(tickers_str, fields)

        return result

    def _connect_if_needed(self):
        if not self.connected:
            self.connect()

    def _assert_is_connected(self):
        if not self.connected:
            raise BloombergError("Connection to Bloomberg was not successful.")
