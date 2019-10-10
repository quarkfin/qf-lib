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

from datetime import datetime
from typing import Sequence, Dict, List

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI, SECURITY, FIELD_DATA, FUT_CHAIN
from qf_lib.data_providers.bloomberg.helpers import set_tickers, set_fields, get_response_events, \
    check_event_for_errors, extract_security_data, check_security_data_for_errors, convert_to_bloomberg_date


class FuturesDataProvider(object):

    def __init__(self, session):
        self._session = session
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get(self, tickers: Sequence[str], chain_date: datetime) -> Dict[str, List[str]]:
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("ReferenceDataRequest")

        set_tickers(request, tickers)
        set_fields(request, ["FUT_CHAIN"])

        # Set the parameters to include all the future contracts, that already expired
        override_fields = ("fieldId", "value")
        override_names = ("CHAIN_DATE", "INCLUDE_EXPIRED_CONTRACTS")
        override_values = (convert_to_bloomberg_date(chain_date), "Y")
        self._set_overrides(request, override_fields, override_names, override_values)

        self._session.sendRequest(request)

        # Return dictionary mapping the tickers to lists of futures chains tickers
        return self._receive_futures_response()

    def _set_overrides(self, request, override_fields, override_names, override_values):
        overrides = request.getElement("overrides")

        for parameters in zip(override_names, override_values):
            override = overrides.appendElement()
            for field, value in zip(override_fields, parameters):
                override.setElement(field, value)

    def _receive_futures_response(self):
        response_events = get_response_events(self._session)
        ticker_to_futures_chain = {}

        for event in response_events:
            check_event_for_errors(event)
            security_data_array = extract_security_data(event)
            check_security_data_for_errors(security_data_array)

            for i in range(security_data_array.numValues()):
                security_data = security_data_array.getValueAsElement(i)
                check_security_data_for_errors(security_data)

                security_name = security_data.getElementAsString(SECURITY)
                future_chain_array = security_data.getElement(FIELD_DATA).getElement(FUT_CHAIN)

                ticker_to_futures_chain[security_name] = []

                for j in range(future_chain_array.numValues()):
                    future_ticker = future_chain_array.getValueAsElement(j)
                    ticker_value = future_ticker.getElementAsString("Security Description")

                    ticker_to_futures_chain[security_name].append(ticker_value)

        return ticker_to_futures_chain
