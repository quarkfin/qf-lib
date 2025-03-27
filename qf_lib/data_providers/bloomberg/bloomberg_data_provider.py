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

from pandas import isnull

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.exchange_rate_provider import ExchangeRateProvider
from qf_lib.data_providers.futures_data_provider import FuturesDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider
from qf_lib.settings import Settings

try:
    import blpapi

    from qf_lib.data_providers.bloomberg.futures_data_provider import BloombergFuturesDataProvider
    from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider
    from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider
    from qf_lib.data_providers.bloomberg.exceptions import BloombergError
    from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI
    from qf_lib.data_providers.bloomberg.helpers import convert_to_bloomberg_date

    is_blpapi_installed = True
except ImportError:
    is_blpapi_installed = False


class BloombergDataProvider(AbstractPriceDataProvider, TickersUniverseProvider,
                            FuturesDataProvider, ExchangeRateProvider):
    """
    Data Provider which provides financial data from Bloomberg.
    """

    def __init__(self, settings: Settings, timer: Optional[Timer] = None):
        super().__init__(timer)
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
            self._futures_data_provider = BloombergFuturesDataProvider(self.session)
        else:
            self.session = None
            self._historical_data_provider = None
            self._reference_data_provider = None
            self._futures_data_provider = None

            warnings.warn(
                "No Bloomberg API installed. If you would like to use BloombergDataProvider first install the blpapi"
                " library")
            exit(1)

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
                                expiration_date_fields: Union[str, Sequence[str]]) -> (
            Dict)[BloombergFutureTicker, QFDataFrame]:
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
        futures_expiration_dates = self.get_current_values(all_specific_tickers, expiration_date_fields).dropna(
            how="all")

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
                           fields: Union[str, Sequence[str]], overrides: Optional[Dict[str, str]] = None,
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
        overrides: Optional[Dict[str, str]]
            A dictionary where each key is a field name (as a string) that corresponds to a default field in the
            Bloomberg request, and the value is the new value (as a string) to override the default value for that field.
            The dictionary allows for multiple fields to be overridden at once, with each key representing a specific
            field to be modified, and the associated value specifying the replacement value for that field.
            If not provided, the default values for all fields will be used.

        Raises
        -------
        BloombergError
            When couldn't get the data from Bloomberg Service
        """
        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        overrides = overrides or {}
        override_name = list(overrides.keys())
        override_value = list(overrides.values())
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

    def create_exchange_rate_ticker(self, base_currency: str, quote_currency: str) -> BloombergTicker:
        return BloombergTicker.from_string(f'{base_currency}{quote_currency} Curncy', security_type=SecurityType.FX)

    def get_last_available_exchange_rate(self, base_currency: str, quote_currency: str,
                                         frequency: Frequency = Frequency.DAILY):
        """
        Get last available exchange rate from the base currency to the quote currency in the provided frequency.

        Parameters
        -----------
        base_currency: str
            ISO code of the base currency (ex. 'USD' for US Dollar)
        quote_currency: str
            ISO code of the quote currency (ex. 'EUR' for Euro)
        frequency: Frequency
            frequency of the returned data

        Returns
        -------
        float
            last available exchange rate
        """
        currency_ticker = self.create_exchange_rate_ticker(base_currency, quote_currency)
        quote_factor = self.get_current_values(currency_ticker, fields="QUOTE_FACTOR")
        return self.get_last_available_price(currency_ticker, frequency=frequency) / quote_factor

    def get_history(self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = None,
                    currency: str = None, overrides: Optional[Dict] = None, look_ahead_bias: bool = False, **kwargs) \
            -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical data from Bloomberg from the (start_date - end_date) time range. In case of frequency, which is
        higher than daily frequency (intraday data), the data is indexed by the start_date. E.g. Time range: 8:00 - 8:01,
        frequency: 1 minute - indexed with the 8:00 timestamp

        Parameters
        ----------
        tickers: Ticker, Sequence[Ticker]
            Tickers' of securities which should be retrieved.
        fields: None, str, Sequence[str]
            Fields of securities which should be retrieved. If None, all available fields will be returned
            (only supported by few DataProviders).
        start_date: datetime
            Date representing the beginning of historical period from which data should be retrieved.
        end_date: datetime
            Date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used.
        frequency: Frequency
            Frequency of the data. It defaults to DAILY.
        currency: str
        overrides: Optional[Dict[str, str]]
            A dictionary where each key is a field name (as a string) that corresponds to a default field in the
            Bloomberg request, and the value is the new value (as a string) to override the default value for that field.
            The dictionary allows for multiple fields to be overridden at once, with each key representing a specific
            field to be modified, and the associated value specifying the replacement value for that field.
            If not provided, the default values for all fields will be used.
        look_ahead_bias: bool
            If set to False, the look-ahead bias will be taken care of to make sure no future data is returned.
        Returns
        -------
        QFSeries, QFDataFrame, QFDataArray
            If possible the result will be squeezed, so that instead of returning QFDataArray, data of lower
            dimensionality will be returned. The results will be either an QFDataArray (with 3 dimensions: date, ticker,
            field), a QFDataFrame (with 2 dimensions: date, ticker or field; it is also possible to get 2 dimensions
            ticker and field if single date was provided) or QFSeries (with 1 dimensions: date).
            If no data is available in the database or a non existing ticker was provided an empty structure
            (QFSeries, QFDataFrame or QFDataArray) will be returned returned.
        """
        if fields is None:
            raise ValueError("Fields being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        frequency = frequency or self.frequency or Frequency.DAILY
        original_end_date = (end_date or self.timer.now()) + RelativeDelta(second=0, microsecond=0)
        end_date = original_end_date if look_ahead_bias else self.get_end_date_without_look_ahead(original_end_date,
                                                                                                  frequency)
        start_date = self._adjust_start_date(start_date, frequency)

        got_single_date = self._got_single_date(start_date, original_end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        def current_ticker(t: BloombergTicker):
            return t.get_current_specific_ticker() if isinstance(t, BloombergFutureTicker) else t

        tickers_mapping = {current_ticker(t): t for t in tickers}

        overrides = overrides or {}
        override_names = list(overrides.keys())
        override_values = list(overrides.values())

        data_array = self._historical_data_provider.get(
            tickers, fields, start_date, end_date, frequency, currency, override_names, override_values)
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

    def price_field_to_str_map(self) -> Dict[PriceField, str]:
        price_field_dict = {
            PriceField.Open: 'PX_OPEN',
            PriceField.High: 'PX_HIGH',
            PriceField.Low: 'PX_LOW',
            PriceField.Close: 'PX_LAST',
            PriceField.Volume: 'PX_VOLUME'
        }
        return price_field_dict

    def get_tickers_universe(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None,
                             display_figi: bool = False) -> List[BloombergTicker]:
        """
        Returns a list of all members of an index. It will not return any data for indices with more than
        20,000 members.

        Parameters
        ----------
        universe_ticker: Ticker
            The ticker symbol representing the index or universe for which the tickers are being queried.
        date: datetime
            The date for which the tickers' universe data is requested.
        display_figi: bool
            The following flag can be used to have this field return Financial Instrument Global Identifiers (FIGI).
            By default set to False, which results in returning tickers identifiers instead of FIGI.

        Returns
        -------
        List[Ticker]
            A list of tickers (Ticker objects) that were included in the index on the specified date.
        """
        members_and_weights = self._get_index_members_and_weights(universe_ticker, date, display_figi)
        return members_and_weights.index.tolist()

    def get_tickers_universe_with_weights(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None,
                                          display_figi: bool = False) -> QFSeries:
        """
        Returns the tickers belonging to a specified universe, along with their corresponding weights, at a given date.
        The result is a QFSeries indexed by ticker objects, with the values representing the respective weights of
        each ticker in the universe.

        Important: It will not return any data for indices with more than 20,000 members.

        Parameters
        ----------
        universe_ticker: Ticker
            The ticker symbol representing the index or universe for which the tickers are being queried.
        date: datetime
            The date for which the tickers' universe data is requested. If not provided, it defaults to current date.
        display_figi: bool
            The following flag can be used to have this field return Financial Instrument Global Identifiers (FIGI).
            By default set to False, which results in returning tickers identifiers instead of FIGI.

        Returns
        -------
        QFSeries
            A QFSeries indexed by Ticker objects, where the values are the weights of the respective tickers
            in the universe at a given date.
        """
        return self._get_index_members_and_weights(universe_ticker, date, display_figi)

    def get_unique_tickers(self, universe_ticker: Ticker) -> List[Ticker]:
        raise NotImplementedError("get_unique_tickers is not supported by BloombergDataProvider.")

    def get_tabular_data(self, ticker: BloombergTicker, field: str,
                         overrides: Optional[Dict[str, str]] = None) -> List:
        """
        Provides current tabular data from Bloomberg. It is a wrapper around get_current_values.

        Parameters
        -----------
        ticker: BloombergTicker
            ticker for security that should be retrieved
        field: str
            field of security that should be retrieved
        overrides: Optional[Dict[str, str]]
            A dictionary where each key is a field name (as a string) that corresponds to a default field in the
            Bloomberg request, and the value is the new value (as a string) to override the default value for that field.
            The dictionary allows for multiple fields to be overridden at once, with each key representing a specific
            field to be modified, and the associated value specifying the replacement value for that field.
            If not provided, the default values for all fields will be used.

        Returns
        -------
        List
            tabular data for the given ticker and field
        """
        tabular_data = self.get_current_values(ticker, field, overrides)
        if not isinstance(tabular_data, list):
            if isnull(tabular_data):
                return []
            else:
                raise ValueError("The requested field does not return tabular data. Please use get_current_values() "
                                 "instead.")
        return tabular_data

    def _get_index_members_and_weights(self, universe_ticker: BloombergTicker, date: Optional[datetime] = None,
                                       display_figi: bool = False) -> QFSeries:
        date = date or datetime.now()
        field = 'INDEX_MEMBERS_WEIGHTS'

        MAX_PAGE_NUMBER = 7
        MAX_MEMBERS_PER_PAGE = 3000
        universe = []

        def str_to_bbg_ticker(identifier: str, figi: bool):
            ticker_str = f"/bbgid/{identifier}" if figi else f"{identifier} Equity"
            return BloombergTicker(ticker_str, SecurityType.STOCK, 1)

        for page_no in range(1, MAX_PAGE_NUMBER + 1):
            ticker_data = self.get_tabular_data(universe_ticker, field, {
                "END_DT": convert_to_bloomberg_date(date),
                "PAGE_NUMBER_OVERRIDE": page_no,
                "DISPLAY_ID_BB_GLOBAL_OVERRIDE": "Y" if display_figi else "N"
            })

            df = QFDataFrame(ticker_data) if len(ticker_data) > 0 else QFDataFrame(columns=["Index Member", "Weight"])
            df = df.set_index("Index Member")
            df.index = df.index.map(lambda s: str_to_bbg_ticker(s, display_figi))
            universe.append(df)
            if len(df) < MAX_MEMBERS_PER_PAGE:
                break

        universe_series = pd.concat(universe).iloc[:, 0]
        return universe_series

    def _connect_if_needed(self):
        if not self.connected:
            self.connect()

    def _assert_is_connected(self):
        if not self.connected:
            raise BloombergError("Connection to Bloomberg was not successful.")
