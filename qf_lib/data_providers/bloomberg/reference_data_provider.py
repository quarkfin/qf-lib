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

import numpy as np
import pandas as pd

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.data_providers.bloomberg.helpers import *


class ReferenceDataProvider(object):
    """
    Used for providing current price data from Bloomberg.
    """

    def __init__(self, session):
        self._session = session

    def get(self, tickers, fields):
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("ReferenceDataRequest")
        set_tickers(request, tickers)
        set_fields(request, fields)

        self._session.sendRequest(request)
        return self._receive_reference_response(tickers, fields)

    def _receive_reference_response(self, tickers, fields):
        response_events = get_response_events(self._session)

        tickers_fields_container = pd.DataFrame(index=tickers, columns=fields)

        for ev in response_events:
            check_event_for_errors(ev)
            security_data_array = extract_security_data(ev)
            check_security_data_for_errors(security_data_array)

            for i in range(security_data_array.numValues()):
                security_data = security_data_array.getValueAsElement(i)
                check_security_data_for_errors(security_data)

                security_name = security_data.getElementAsString(SECURITY)
                ticker = BloombergTicker.from_string(security_name)
                field_data_array = security_data.getElement(FIELD_DATA)

                for field_name in fields:
                    try:
                        value = field_data_array.getElementAsFloat(field_name)
                    except blpapi.exception.InvalidConversionException:
                        value = field_data_array.getElementAsString(field_name)
                    except blpapi.exception.NotFoundException:
                        value = np.nan

                    tickers_fields_container.loc[ticker, field_name] = value

        return tickers_fields_container
