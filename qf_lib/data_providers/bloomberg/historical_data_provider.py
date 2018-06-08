from datetime import datetime
from typing import Any, Sequence

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI, CURRENCY, START_DATE, END_DATE, \
    PERIODICITY_SELECTION, PERIODICITY_ADJUSTMENT, SECURITY, FIELD_DATA, DATE
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg.helpers import set_tickers, set_fields, convert_to_bloomberg_date, \
    convert_to_bloomberg_freq, get_response_events, check_event_for_errors, check_security_data_for_errors, \
    extract_security_data


class HistoricalDataProvider(object):
    """
    Used for providing historical data from Bloomberg.
    """

    # These revert to the actual date from today (if the end date is left blank) or from the End Date
    # (see PERIODICITY_ADJUSTMENT in blpapi-developers-guide for more)
    PERIODICITY_ADJUSTMENT = "ACTUAL"

    def __init__(self, session):
        self._session = session
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get(
        self, tickers: Sequence[str], fields: Sequence[str], start_date: datetime, end_date: datetime,
        frequency: Frequency, currency: str, override_name: str, override_value: Any
    ) -> pd.Panel:
        """
        Gets historical data from Bloomberg.

        Returns
        -------
        pd.Panel with 3 dimensions: date, ticker, field
        """
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("HistoricalDataRequest")

        set_tickers(request, tickers)
        set_fields(request, fields)

        self._set_time_period(request, start_date, end_date, frequency)
        self._set_currency(currency, request)

        if override_name is not None:
            self._set_override(request, override_name, override_value)

        self._session.sendRequest(request)
        data_panel = self._receive_historical_response(fields)
        return data_panel

    @classmethod
    def _set_currency(cls, currency, request):
        if currency is not None:
            request.set(CURRENCY, currency)

    @classmethod
    def _set_time_period(cls, request, start_date, end_date, frequency):
        start_date_str = convert_to_bloomberg_date(start_date)
        end_date_str = convert_to_bloomberg_date(end_date)
        frequency_bloomberg = convert_to_bloomberg_freq(frequency)

        request.set(START_DATE, start_date_str)
        request.set(END_DATE, end_date_str)
        request.set(PERIODICITY_SELECTION, frequency_bloomberg)
        request.set(PERIODICITY_ADJUSTMENT, cls.PERIODICITY_ADJUSTMENT)

    @classmethod
    def _set_override(cls, request, override_name, override_value):
        overrides = request.getElement("overrides")
        override = overrides.appendElement()
        override.setElement("fieldId", override_name)
        override.setElement("value", override_value)

    @staticmethod
    def _get_float_or_nan(element, field_name):
        if element.hasElement(field_name):
            return element.getElementAsFloat(field_name)
        else:
            return float("nan")

    def _receive_historical_response(self, fields):
        response_events = get_response_events(self._session)

        tickers_to_data_dict = {}

        for event in response_events:
            check_event_for_errors(event)
            security_data = extract_security_data(event)

            try:
                check_security_data_for_errors(security_data)
            except BloombergError:
                security_name = security_data.getElementAsString(SECURITY)
                ticker = BloombergTicker.from_string(security_name)
                tickers_to_data_dict[ticker] = pd.DataFrame()
                self.logger.exception("Error in the received historical response")

            security_name = security_data.getElementAsString(SECURITY)
            field_data_array = security_data.getElement(FIELD_DATA)
            field_data_list = \
                [field_data_array.getValueAsElement(i) for i in range(0, field_data_array.numValues())]
            out_dates = [x.getElementAsDatetime(DATE) for x in field_data_list]

            single_ticker_data = pd.DataFrame(index=out_dates, columns=fields)

            for fieldName in fields:
                single_ticker_data[fieldName] = [self._get_float_or_nan(x, fieldName) for x in field_data_list]

            single_ticker_data.replace('#N/A History', pd.np.nan, inplace=True)
            single_ticker_data.index = pd.to_datetime(single_ticker_data.index)

            ticker = BloombergTicker.from_string(security_name)
            tickers_to_data_dict[ticker] = single_ticker_data

        return self._tickers_dict_to_panel(tickers_to_data_dict)

    @staticmethod
    def _tickers_dict_to_panel(tickers_to_data_dict: dict) -> pd.Panel:
        """
        Converts a dictionary tickers->DateFrame to Panel.

        Parameters
        ----------
        tickers_to_data_dict: dict[str, pd.DataFrame]

        Returns
        -------
        pandas.Panel  [date, ticker, field]
        """
        tickers_panel = pd.Panel.from_dict(data=tickers_to_data_dict)

        # recombines dimensions, so that the first one is date
        # major is ticker
        # minor is field
        return tickers_panel.transpose(1, 0, 2)
