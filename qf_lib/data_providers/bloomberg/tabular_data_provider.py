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

from typing import List

from qf_lib.data_providers.bloomberg.bloomberg_names import FIELD_DATA, REF_DATA_SERVICE_URI
from qf_lib.data_providers.bloomberg.helpers import get_response_events, check_event_for_errors, extract_security_data, \
    check_security_data_for_errors, set_tickers, set_fields


class TabularDataProvider:
    """
    Used for providing current tabular data from Bloomberg.
    Handles requests containing only one ticker and one field.

    Was tested on 'INDX_MEMBERS' and 'MERGERS_AND_ACQUISITIONS' requests. There is no guarantee that
    all other request will be handled, as returned data structures might vary.
    """

    def __init__(self, session):
        self._session = session

    def get(self, tickers, fields, override_names, override_values) -> List:
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("ReferenceDataRequest")
        set_tickers(request, tickers)
        set_fields(request, fields)

        if override_names is not None:
            overrides = request.getElement("overrides")
            for override_name, override_value in zip(override_names, override_values):
                override = overrides.appendElement()
                override.setElement("fieldId", override_name)
                override.setElement("value", override_value)

        self._session.sendRequest(request)
        return self._receive_reference_response(fields)

    def _receive_reference_response(self, fields):
        response_events = get_response_events(self._session)

        elements = []

        for ev in response_events:
            check_event_for_errors(ev)
            security_data_array = extract_security_data(ev)
            check_security_data_for_errors(security_data_array)

            for i in range(security_data_array.numValues()):
                security_data = security_data_array.getValueAsElement(i)
                check_security_data_for_errors(security_data)

                field_data_array = security_data.getElement(FIELD_DATA)

                for field_name in fields:
                    array = field_data_array.getElement(field_name)
                    for element in array.values():
                        keys_values_dict = {}
                        for elem in element.elements():
                            key = elem.name().__str__()
                            value = element.getElementAsString(key)
                            keys_values_dict[key] = value
                        elements.append(keys_values_dict)

        return elements
