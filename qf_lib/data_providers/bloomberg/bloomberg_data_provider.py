import warnings
from datetime import datetime
from typing import Union, Sequence, Dict

import blpapi
import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker, tickers_as_strings
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI
from qf_lib.data_providers.bloomberg.historical_data_provider import HistoricalDataProvider
from qf_lib.data_providers.bloomberg.reference_data_provider import ReferenceDataProvider, BloombergError
from qf_lib.settings import Settings


class BloombergDataProvider(AbstractPriceDataProvider):
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

        # to keep the order of tickers and fields we reindex the panel
        data_frame = data_frame.reindex(index=tickers, columns=fields)

        # squeeze unused dimensions
        tickers_indices = 0 if got_single_ticker else slice(None)
        fields_indices = 0 if got_single_field else slice(None)
        squeezed_result = data_frame.iloc[tickers_indices, fields_indices]

        casted_result = self._cast_result_to_proper_type(squeezed_result)

        return casted_result

    def get_history(
        self, tickers: Union[BloombergTicker, Sequence[BloombergTicker]], fields: Union[str, Sequence[str]],
            start_date: datetime, end_date: datetime=None, frequency: Frequency=Frequency.DAILY, currency: str=None,
            override_name: str=None, override_value: str=None)\
            -> Union[QFSeries, QFDataFrame, pd.Panel]:

        self._connect_if_needed()
        self._assert_is_connected()

        got_single_date = (start_date == end_date)

        tickers, got_single_ticker = convert_to_list(tickers, BloombergTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        start_date, end_date = self._clean_dates(start_date, end_date)

        tickers_str = tickers_as_strings(tickers)
        data_panel = self._historical_data_provider.get(
            tickers_str, fields, start_date, end_date, frequency, currency, override_name, override_value)

        # to keep the order of tickers and fields we reindex the panel
        data_panel = data_panel.reindex(major_axis=tickers, minor_axis=fields)

        squeezed_result = self._squeeze_panel(data_panel, got_single_date, got_single_ticker, got_single_field)
        casted_result = self._cast_result_to_proper_type(squeezed_result)

        return casted_result

    def supported_ticker_types(self):
        return {BloombergTicker}

    def price_field_to_str_map(self, ticker: BloombergTicker=None) -> Dict[PriceField, str]:
        price_field_dict = {
            PriceField.Open: 'PX_OPEN',
            PriceField.High: 'PX_HIGH',
            PriceField.Low: 'PX_LOW',
            PriceField.Close: 'PX_LAST',
            PriceField.Volume: 'PX_VOLUME'
        }
        return price_field_dict

    def _connect_if_needed(self):
        if not self.connected:
            self.connect()

    def _assert_is_connected(self):
        if not self.connected:
            raise BloombergError("Connection to Bloomberg was not successful.")

    def _clean_dates(self, start_date, end_date):
        if end_date is None:
            end_date = datetime.now()

        start_date = self._convert_to_datetime(start_date)
        end_date = self._convert_to_datetime(end_date)

        return start_date, end_date

    @staticmethod
    def _convert_to_datetime(converted_date):
        if isinstance(converted_date, str):
            warnings.warn(
                "All dates should be in datetime format. String dates won't be supported in the future",
                DeprecationWarning
            )
            converted_date = str_to_date(converted_date)

        return converted_date
