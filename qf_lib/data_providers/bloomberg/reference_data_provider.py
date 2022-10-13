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
from typing import Sequence, Dict, Any

import blpapi
import numpy as np
from blpapi import DataType
from pandas import to_datetime

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI, SECURITY, FIELD_DATA
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg.helpers import set_tickers, set_fields, get_response_events, \
    check_event_for_errors, extract_security_data, check_security_data_for_errors


class ReferenceDataProvider:
    """ Used for providing current price data from Bloomberg. """

    def __init__(self, session):
        self._session = session
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get(self, tickers: Sequence[BloombergTicker], fields,  override_name: str = None, override_value: Any = None):
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("ReferenceDataRequest")

        tickers_str = [t.as_string() for t in tickers]
        set_tickers(request, tickers_str)
        set_fields(request, fields)
        if override_name is not None:
            self._set_override(request, override_name, override_value)

        self._session.sendRequest(request)
        return self._receive_reference_response(tickers, fields)

    def _receive_reference_response(self, tickers, fields):
        ticker_str_to_ticker: Dict[str, BloombergTicker] = {t.as_string(): t for t in tickers}

        response_events = get_response_events(self._session)
        tickers_fields_container = QFDataFrame(index=tickers, columns=fields)

        for ev in response_events:
            try:
                check_event_for_errors(ev)
                security_data_array = extract_security_data(ev)
                check_security_data_for_errors(security_data_array)

                for security_data in security_data_array.values():
                    try:
                        field_data_array = security_data.getElement(FIELD_DATA)
                        security_name = security_data.getElementAsString(SECURITY) if \
                            security_data.hasElement(SECURITY, True) else None

                        ticker = ticker_str_to_ticker[security_name]
                        for field_name in fields:
                            value = self._parse_value(field_data_array, field_name)
                            tickers_fields_container.loc[ticker, field_name] = value

                    except KeyError:
                        self.logger.warning("Received data for a ticker which was not present in the request. "
                                            "The data for that ticker will be excluded from parsing.")
                    except BloombergError as e:
                        self.logger.error(e)

            except BloombergError as e:
                self.logger.error(e)

        return tickers_fields_container.infer_objects()

    @classmethod
    def _set_override(cls, request, override_name, override_value):
        overrides = request.getElement("overrides")
        override = overrides.appendElement()
        override.setElement("fieldId", override_name)
        override.setElement("value", override_value)

    @staticmethod
    def _parse_value(field_data_array, field_name):
        if not field_data_array.hasElement(field_name, True):
            return None
        field_element = field_data_array.getElement(field_name)
        element_data_type = field_element.datatype()
        try:
            if element_data_type in (DataType.FLOAT32, DataType.FLOAT64):
                value = field_element.getValueAsFloat()
            elif element_data_type in (DataType.INT32, DataType.INT64):
                value = field_element.getValueAsInteger()
            elif element_data_type is DataType.BOOL:
                value = field_element.getValueAsBool()
            elif element_data_type in (DataType.DATETIME, DataType.TIME, DataType.DATE):
                value = to_datetime(field_element.getValueAsDatetime())
            else:
                value = field_element.getValueAsString()
        except blpapi.exception.NotFoundException:
            value = np.nan

        return value
