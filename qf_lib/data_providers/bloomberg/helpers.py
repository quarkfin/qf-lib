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

import datetime

import blpapi
import numpy as np
from blpapi import DataType

from qf_lib.common.enums.frequency import Frequency
from qf_lib.data_providers.bloomberg.bloomberg_names import SECURITIES, SECURITY, FIELDS, RESPONSE_ERROR, SECURITY_DATA, \
    BAR_DATA, FIELD_EXCEPTIONS, SECURITY_ERROR
from qf_lib.data_providers.bloomberg.exceptions import BloombergError


def set_tickers(request, tickers):
    """
    Sets requested tickers in the Bloomberg's request.

    Parameters
    ----------
    request
        request to be sent
    tickers: List[str]
        required tickers

    """
    securities = request.getElement(SECURITIES)
    for ticker in tickers:
        securities.appendValue(ticker)


def set_ticker(request, ticker):
    """
    Sets requested ticker in the Bloomberg's request.

    Parameters
    ----------
    request
        request to be sent
    ticker: str
        required ticker

    """
    security = request.getElement(SECURITY)
    security.setValue(ticker)


def set_fields(request, field_names):
    requested_fields = request.getElement(FIELDS)
    for field in field_names:
        requested_fields.appendValue(field)


def convert_to_bloomberg_freq(frequency: Frequency) -> str:
    frequency_to_bloomberg = {
        Frequency.MIN_1: "1",
        Frequency.MIN_5: "5",
        Frequency.MIN_10: "10",
        Frequency.MIN_15: "15",
        Frequency.MIN_30: "30",
        Frequency.MIN_60: "60",
        Frequency.DAILY: "DAILY",
        Frequency.WEEKLY: "WEEKLY",
        Frequency.MONTHLY: "MONTHLY",
        Frequency.QUARTERLY: "QUARTERLY",
        Frequency.SEMI_ANNUALLY: "SEMI_ANNUALLY",
        Frequency.YEARLY: "YEARLY",
    }

    return frequency_to_bloomberg[frequency]


def convert_to_bloomberg_date(date: datetime) -> str:
    return date.strftime('%Y%m%d')


def check_event_for_errors(event):
    num_of_messages = sum(1 for _ in event)
    if num_of_messages != 1:
        error_message = "Number of messages != 1"
        raise BloombergError(error_message)

    first_msg = next(blpapi.event.MessageIterator(event))

    if first_msg.asElement().hasElement(RESPONSE_ERROR):
        error_message = "Response error: " + str(first_msg.asElement())
        raise BloombergError(error_message)


def extract_security_data(event):
    first_msg = next(blpapi.event.MessageIterator(event))
    return first_msg.getElement(SECURITY_DATA)


def extract_bar_data(event):
    first_msg = next(blpapi.event.MessageIterator(event))
    return first_msg.getElement(BAR_DATA)


def get_response_events(session):
    response_events = []
    while True:
        event = session.nextEvent()
        if event.eventType() == blpapi.event.Event.PARTIAL_RESPONSE:
            response_events.append(event)
        elif event.eventType() == blpapi.event.Event.RESPONSE:
            response_events.append(event)
            break

    return response_events


def check_security_data_for_errors(security_data):
    if security_data.hasElement(SECURITY_ERROR):
        error_message = "Response contains security error:\n" + str(security_data)
        raise BloombergError(error_message)


def get_field_exceptions_from_security_data(security_data):
    if security_data.hasElement(FIELD_EXCEPTIONS):
        field_exceptions = security_data.getElement(FIELD_EXCEPTIONS)
        return field_exceptions if field_exceptions.numValues() > 0 else None


def convert_field(field_data_array, field_name):
    if not field_data_array.hasElement(field_name, True):
        return None
    field_element = field_data_array.getElement(field_name)
    element_data_type = field_element.datatype()

    type_to_function = {
        DataType.FLOAT32: 'getValueAsFloat',
        DataType.FLOAT64: 'getValueAsFloat',
        DataType.INT32: 'getValueAsInteger',
        DataType.INT64: 'getValueAsInteger',
        DataType.BOOL: 'getValueAsBool',
        DataType.STRING: 'getValueAsString',
        DataType.DATETIME: 'getValueAsDatetime',
        DataType.TIME: 'getValueAsDatetime',
        DataType.DATE: 'getValueAsDatetime',
    }

    try:
        if element_data_type is DataType.SEQUENCE:
            value = []
            for element in field_element.values():
                keys_values_dict = {}
                for elem in element.elements():
                    key = elem.name().__str__()
                    keys_values_dict[key] = convert_field(element, key)
                value.append(keys_values_dict)
        else:
            _fun = type_to_function.get(element_data_type, 'getValueAsString')
            value = getattr(field_element, _fun)()
            if isinstance(value, datetime.date):
                value = datetime.datetime.combine(value, datetime.datetime.min.time())
    except blpapi.exception.NotFoundException:
        value = np.nan

    return value
