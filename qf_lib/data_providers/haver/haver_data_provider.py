import os
import threading
import warnings
from datetime import datetime
from typing import Union, Sequence, Dict, Optional

from pandas import PeriodIndex, DataFrame

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import HaverTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.settings import Settings

try:
    import Haver
    is_haver_installed = True
except ImportError:
    is_haver_installed = False
    warnings.warn("No Haver installed.")


class HaverDataProvider(AbstractPriceDataProvider):

    get_lock = threading.Lock()

    def __init__(self, settings: Settings):
        """
        Constructs a new ``HaverDataProvider`` instance.

        Parameters
        ----------
        db_location - A path to the directory containing the Haver database.
        """
        self.db_location = settings.haver_path
        self.connected = False

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_history(self, tickers: Union[HaverTicker, Sequence[HaverTicker]], fields=None, start_date: datetime=None,
                    end_date: datetime=None, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        fields:
            field should None as each ticker corresponds to one timeseries and there is no such thing as a field in
            the Haver DB.

        this method will never return a QFDataArray.
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
