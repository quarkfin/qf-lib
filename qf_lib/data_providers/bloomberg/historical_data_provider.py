from datetime import datetime
from typing import Any, Sequence

import numpy as np
import pandas as pd
import xarray as xr

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
    ) -> xr.DataArray:
        """
        Gets historical data from Bloomberg.

        Returns
        -------
        DataArray with 3 dimensions: date, ticker, field
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
        data_panel = self._receive_historical_response(tickers, fields)
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
            result = element.getElementAsFloat(field_name)
            if result == '#N/A History':
                result = float('nan')
        else:
            result = float("nan")

        return result

    def _receive_historical_response(self, requested_tickers, requested_fields):
        response_events = get_response_events(self._session)

        tickers_dates_fields_data_dict = dict()

        for event in response_events:
            check_event_for_errors(event)
            security_data = extract_security_data(event)

            security_name = security_data.getElementAsString(SECURITY)
            ticker = BloombergTicker.from_string(security_name)

            try:
                check_security_data_for_errors(security_data)

                field_data_array = security_data.getElement(FIELD_DATA)
                field_data_list = \
                    [field_data_array.getValueAsElement(i) for i in range(field_data_array.numValues())]
                dates = [pd.to_datetime(x.getElementAsDatetime(DATE)) for x in field_data_list]

                data = np.empty((len(dates), len(requested_fields)))
                data[:] = np.nan

                dates_fields_values = xr.DataArray(
                    data, coords={'dates': dates, 'fields': requested_fields}, dims=('dates', 'fields')
                )

                for field_name in requested_fields:
                    dates_fields_values.loc[:, field_name] = [
                        self._get_float_or_nan(data_of_date_elem, field_name) for data_of_date_elem in field_data_list
                    ]

                tickers_dates_fields_data_dict[ticker] = dates_fields_values

            except BloombergError:
                self.logger.exception("Error in the received historical response")

        return self._tickers_dict_to_data_array(tickers_dates_fields_data_dict, requested_tickers, requested_fields)

    @staticmethod
    def _tickers_dict_to_data_array(tickers_dates_fields_data_dict, requested_tickers, requested_fields
                                    ) -> xr.DataArray:
        """
        Converts a dictionary tickers->DateFrame to xarray.DataArray.

        Parameters
        ----------
        tickers_dates_fields_data_dict: ticker -> date -> field -> number mapping

        Returns
        -------
        DataArray  [date, ticker, field]
        """
        # return empty xr.DataArray if there is no data to be converted
        if not tickers_dates_fields_data_dict:
            data = np.empty((0, len(requested_tickers), len(requested_fields)))
            data[:] = np.nan
            return xr.DataArray(
                data, coords={'dates': [], 'tickers': requested_tickers, 'fields': requested_fields},
                dims=('dates', 'tickers', 'fields')
            )

        tickers, data_arrays = zip(
            *((ticker, data_array) for ticker, data_array in tickers_dates_fields_data_dict.items())
        )

        tickers_index = pd.Index(tickers, name='tickers')
        result = xr.concat(data_arrays, dim=tickers_index)  # type: xr.DataArray
        result = result.transpose('dates', 'tickers', 'fields')

        return result

    @staticmethod
    def _get_subdictionary(dictionary, key):
        subdictionary = dictionary.get(key, None)
        if subdictionary is None:
            subdictionary = dict()
            dictionary[key] = subdictionary

        return subdictionary
