from datetime import datetime
from typing import Union, Sequence, Dict, List

import blpapi

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker, tickers_as_strings
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI
from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider
from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider, BloombergError
from qf_lib.data_providers.bloomberg.tabular_data_provider import TabularDataProvider
from qf_lib.data_providers.helpers import normalize_data_array, cast_dataframe_to_proper_type
from qf_lib.data_providers.tickers_universe_provider import TickersUniverseProvider
from qf_lib.settings import Settings


class BloombergDataProvider(AbstractPriceDataProvider, TickersUniverseProvider):
    """
    Provides financial data from the Bloomberg.
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
        if fields is None:
            raise ValueError("Fields being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        got_single_date = start_date is not None and (start_date == end_date)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        if end_date is None:
            end_date = datetime.now()

        tickers_str = tickers_as_strings(tickers)
        data_array = self._historical_data_provider.get(
            tickers_str, fields, start_date, end_date, frequency, currency, override_name, override_value)

        normalized_result = normalize_data_array(
            data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field
        )

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

    def get_tickers_universe(self, universe_name: BloombergTicker, date: datetime) -> List[BloombergTicker]:
        if date.date() != datetime.today().date():
            raise ValueError("BloombergDataProvider does not provide historical tickers_universe data")
        field = 'INDX_MEMBERS'
        ticker_names = self.get_tabular_data(universe_name, field)
        tickers = [BloombergTicker(name + " Equity") for name in ticker_names]
        return tickers

    def get_tabular_data(self, ticker: BloombergTicker, field: str):

        if field is None:
            raise ValueError("Field being None is not supported by {}".format(self.__class__.__name__))

        self._connect_if_needed()
        self._assert_is_connected()

        tickers, got_single_ticker = convert_to_list(ticker, BloombergTicker)
        fields, got_single_field = convert_to_list(field, (PriceField, str))

        tickers_str = tickers_as_strings(tickers)
        data_array = self._tabular_data_provider.get(tickers_str, fields)

        return data_array

    def _connect_if_needed(self):
        if not self.connected:
            self.connect()

    def _assert_is_connected(self):
        if not self.connected:
            raise BloombergError("Connection to Bloomberg was not successful.")
