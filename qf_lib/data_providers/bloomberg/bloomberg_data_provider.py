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
from typing import Union, Sequence, Dict, List
from pandas import to_datetime

import blpapi

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker, tickers_as_strings
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future import FutureContract
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI
from qf_lib.data_providers.bloomberg.futures_data_provider import FuturesDataProvider
from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider
from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider, BloombergError
from qf_lib.data_providers.bloomberg.tabular_data_provider import TabularDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider
from qf_lib.settings import Settings


class BloombergDataProvider(AbstractPriceDataProvider, TickersUniverseProvider):
    """
    Provides financial data from Bloomberg.
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

    def get_futures(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], start_date: datetime,
                    end_date: datetime = None, frequency: Frequency = Frequency.DAILY, currency: str = None) -> \
            Dict[BloombergTicker, FuturesChain]:
        """
        Provides data related to future chains for each of the given tickers, within a given time range. It gets the
        values of price fields (open, high, low, close, volume) and expiration date for each future contract.

        Parameters
        ----------
        tickers
            tickers for future chains which should be retrieved
        start_date
        end_date
            time range used to download the historical data prices
        frequency
            frequency of the historical
        currency
            currency used to gather the historical data prices

        Returns
        -------
        ticker_to_futures_chain: Dict[BloombergTicker, FuturesChain]

        Raises
        -------
        BloombergError
            When couldn't get the data from Bloomberg Service
        """
        self._connect_if_needed()
        self._assert_is_connected()

        if end_date is None:
            end_date = datetime.now()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        tickers_str = tickers_as_strings(tickers)

        # Dictionary, which maps each bloomberg ticker to corresponding FuturesChain object
        ticker_to_futures_chain = {}  # type: Dict[BloombergTicker, FuturesChain]

        # Get a dictionary, which is mapping tickers to list of tickers related to future contracts
        ticker_to_futures_tickers = self._futures_data_provider.get(tickers_str, end_date)  # type: Dict[str, List[str]]

        for ticker_str, future_tickers_list in ticker_to_futures_tickers.items():

            # Download the historical prices
            fields = [self.price_field_to_str_map(BloombergTicker(ticker_str))[price_field]
                      for price_field in PriceField.ohlcv()]

            future_data_array = self._historical_data_provider.get(future_tickers_list, fields, start_date,
                                                                   end_date, frequency, currency, None, None)

            # Download the last tradeable dates for each of the future contracts (expiration dates)
            EXPIRATION_DATE_FIELD = "LAST_TRADEABLE_DT"
            futures_exp_dates = self._reference_data_provider.get(future_tickers_list, [EXPIRATION_DATE_FIELD])

            # Create a list of expiration dates and a list of futures. These two lists are afterwards combined into a
            # futures chain (at first the data is held in two lists for optimization reasons)
            expiration_dates_list = []
            futures_list = []

            for future_ticker in future_data_array.get_index('tickers'):

                # Create a data frame and cast it into PricesDataFrame
                data = future_data_array.loc[:, future_ticker, :]
                data = cast_dataframe(data.to_pandas().dropna(how="all"), PricesDataFrame)
                data.rename(columns=self.str_to_price_field_map(future_ticker), inplace=True)

                # Find the expiration date for the future contract
                exp_date = str_to_date(futures_exp_dates.loc[future_ticker][EXPIRATION_DATE_FIELD])

                # Create the future object and append it to the list of futures for this ticker
                future = FutureContract(ticker=future_ticker,
                                        exp_date=exp_date,
                                        data=data
                                        )

                futures_list.append(future)
                expiration_dates_list.append(exp_date)

            # Define the FuturesChain and add it to the result dictionary
            futures_chain = FuturesChain(index=to_datetime(expiration_dates_list), data=futures_list)
            ticker_to_futures_chain[BloombergTicker(ticker_str)] = futures_chain

        return ticker_to_futures_chain

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
        historical_data: QFDataFrame/QFSeries

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
        E.g.
        Time range: 8:00 - 8:01, frequency: 1 minute - indexed with the 8:00 timestamp
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

        tickers_str = tickers_as_strings(tickers)
        data_array = self._historical_data_provider.get(
            tickers_str, fields, start_date, end_date, frequency, currency, override_name, override_value)

        normalized_result = normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field)

        return normalized_result

    def supported_ticker_types(self):
        return {BloombergTicker}

    def price_field_to_str_map(self, ticker: BloombergTicker = None) -> Dict[PriceField, str]:
        price_field_dict = {
            PriceField.Open: 'PX_OPEN',
            PriceField.High: 'PX_HIGH',
            PriceField.Low: 'PX_LOW',
            PriceField.Close: 'PX_LAST',
            PriceField.Volume: 'PX_VOLUME'
        }
        return price_field_dict

    def str_to_price_field_map(self, ticker: BloombergTicker = None) -> Dict[PriceField, str]:
        price_field_dict = {
            'PX_OPEN': PriceField.Open,
            'PX_HIGH': PriceField.High,
            'PX_LOW': PriceField.Low,
            'PX_LAST': PriceField.Close,
            'PX_VOLUME': PriceField.Volume
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
