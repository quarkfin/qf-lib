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
from collections import defaultdict
from datetime import datetime
from typing import Any, Sequence, Dict

import numpy as np
import pandas as pd
from pandas import to_datetime

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI, CURRENCY, START_DATE, END_DATE, \
    PERIODICITY_SELECTION, PERIODICITY_ADJUSTMENT, SECURITY, FIELD_DATA, DATE, \
    START_DATE_TIME, END_DATE_TIME, INTERVAL, BAR_TICK_DATA
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg.helpers import set_tickers, set_fields, convert_to_bloomberg_date, \
    convert_to_bloomberg_freq, get_response_events, check_event_for_errors, check_security_data_for_errors, \
    extract_security_data, set_ticker, extract_bar_data
from qf_lib.data_providers.helpers import tickers_dict_to_data_array


class HistoricalDataProvider:
    """ Used for providing historical data from Bloomberg. """

    # These revert to the actual date from today (if the end date is left blank) or from the End Date
    # (see PERIODICITY_ADJUSTMENT in blpapi-developers-guide for more)
    PERIODICITY_ADJUSTMENT = "ACTUAL"

    def __init__(self, session):
        self._session = session
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get(self, tickers: Sequence[BloombergTicker], fields: Sequence[str], start_date: datetime, end_date: datetime,
            frequency: Frequency, currency: str = None, override_name: str = None, override_value: Any = None) \
            -> QFDataArray:
        """ Gets historical data from Bloomberg.

        If the frequency is higher than the daily - the Intraday Bar Request is used, otherwise - the Historical Data
        Request. In case of intraday data, the currency and override parameters should not be used, as none of them
        is a valid Intraday Bar Request parameter.
        """
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        if frequency > Frequency.DAILY:
            assert all(parameter is None for parameter in (currency, override_name, override_value))
            qf_data_array = self._get_intraday_data(ref_data_service, tickers, fields, start_date, end_date, frequency)
        else:
            qf_data_array = self._get_historical_data(ref_data_service, tickers, fields, start_date, end_date,
                                                      frequency, currency, override_name, override_value)
        return qf_data_array

    def _get_historical_data(self, ref_data_service, tickers: Sequence[BloombergTicker], fields: Sequence[str],
                             start_date: datetime, end_date: datetime, frequency: Frequency, currency: str,
                             override_name: str, override_value: Any):
        request = ref_data_service.createRequest("HistoricalDataRequest")

        ticker_strings = [t.as_string() for t in tickers]
        set_tickers(request, ticker_strings)
        set_fields(request, fields)

        self._set_time_period(request, start_date, end_date, frequency)
        self._set_currency(currency, request)
        if override_name is not None:
            self._set_override(request, override_name, override_value)

        self._session.sendRequest(request)
        return self._receive_historical_response(tickers, fields)

    def _get_intraday_data(self, ref_data_service, tickers: Sequence[BloombergTicker], fields, start_date, end_date,
                           frequency):
        """ Sends requests for each ticker and combines the outputs together. """

        tickers_data_dict = dict()

        for ticker in tickers:
            request = ref_data_service.createRequest("IntradayBarRequest")
            set_ticker(request, ticker.as_string())
            self._set_intraday_time_period(request, start_date, end_date, frequency)
            self._session.sendRequest(request)
            tickers_data_dict[ticker] = self._receive_intraday_response(ticker, fields)

        return tickers_dict_to_data_array(tickers_data_dict, list(tickers_data_dict.keys()), fields)

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
    def _set_intraday_time_period(cls, request, start_date, end_date, frequency):
        frequency_bloomberg = convert_to_bloomberg_freq(frequency)

        request.set(START_DATE_TIME, start_date)
        request.set(END_DATE_TIME, end_date)
        request.set(INTERVAL, frequency_bloomberg)

    @classmethod
    def _set_override(cls, request, override_name, override_value):
        overrides = request.getElement("overrides")
        override = overrides.appendElement()
        override.setElement("fieldId", override_name)
        override.setElement("value", override_value)

    @staticmethod
    def _get_float_or_nan_intraday(element, field_name):
        fields_mapping = {
            "PX_LAST": "close",
            "PX_OPEN": "open",
            "PX_LOW": "low",
            "PX_HIGH": "high",
            "PX_VOLUME": "volume"
        }
        if element.hasElement(field_name):
            result = element.getElementAsFloat(field_name)
            if result == '#N/A History':
                result = float('nan')
        elif element.hasElement(fields_mapping[field_name]):
            result = element.getElementAsFloat(fields_mapping[field_name])
            if result == '#N/A History':
                result = float('nan')
        else:
            result = float("nan")

        return result

    @staticmethod
    def _get_float_or_nan(element, field_name):
        if element.hasElement(field_name):
            result = element.getElementAsFloat(field_name)
            if result == '#N/A History':
                result = float('nan')
        else:
            result = float("nan")

        return result

    def _receive_historical_response(self, requested_tickers: Sequence[BloombergTicker], requested_fields: Sequence[str]):
        ticker_str_to_ticker: Dict[str, BloombergTicker] = {t.as_string(): t for t in requested_tickers}

        response_events = get_response_events(self._session)
        tickers_data_dict = defaultdict(lambda: QFDataFrame(columns=requested_fields))

        for event in response_events:
            try:
                check_event_for_errors(event)

                security_data = extract_security_data(event)
                check_security_data_for_errors(security_data)

                field_data_array = security_data.getElement(FIELD_DATA)
                dates = [to_datetime(x.getElementAsDatetime(DATE)) for x in field_data_array.values()]

                dates_fields_values = QFDataFrame(np.nan, index=dates, columns=requested_fields)

                for field_name in requested_fields:
                    dates_fields_values.loc[:, field_name] = [
                        self._get_float_or_nan(data_of_date_elem, field_name)
                        for data_of_date_elem in field_data_array.values()
                    ]
                security_name = security_data.getElementAsString(SECURITY)

                try:
                    ticker = ticker_str_to_ticker[security_name]
                    tickers_data_dict[ticker] = QFDataFrame(pd.concat([dates_fields_values, tickers_data_dict[ticker]]))
                except KeyError:
                    self.logger.warning(f"Received data for a ticker which was not present in the request: "
                                        f"{security_name}. The data for that ticker will be excluded from parsing.")
            except BloombergError as e:
                self.logger.error(e)

        return tickers_dict_to_data_array(tickers_data_dict, list(tickers_data_dict.keys()), requested_fields)

    def _receive_intraday_response(self, requested_ticker: BloombergTicker, requested_fields):
        """ The response for intraday bar is related to a single ticker. """
        response_events = get_response_events(self._session)
        tickers_data_dict = defaultdict(lambda: QFDataFrame(columns=requested_fields))

        for event in response_events:
            try:
                check_event_for_errors(event)
                bar_data = extract_bar_data(event)

                bar_tick_data_array = bar_data.getElement(BAR_TICK_DATA)
                dates = [to_datetime(e.getElementAsDatetime("time")) for e in bar_tick_data_array.values()]
                dates_fields_values = QFDataFrame(np.nan, index=dates, columns=requested_fields)

                for field_name in requested_fields:
                    dates_fields_values.loc[:, field_name] = [
                        self._get_float_or_nan_intraday(data_of_date_elem, field_name)
                        for data_of_date_elem in bar_tick_data_array.values()
                    ]

                df = tickers_data_dict[requested_ticker]
                tickers_data_dict[requested_ticker] = df.append(dates_fields_values)
            except BloombergError as e:
                self.logger.error(e)

        return tickers_data_dict[requested_ticker]
