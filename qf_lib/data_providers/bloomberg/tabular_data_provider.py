from qf_lib.data_providers.bloomberg.helpers import *


class TabularDataProvider(object):
    """
    Used for providing current tabular data from Bloomberg.
    Handles requests containing only one ticker and one field.

    Was tested on 'INDX_MEMBERS' request. There is no guarantee that all other request will be handled,
    as returned data structures might vary.
    """

    def __init__(self, session):
        self._session = session

    def get(self, tickers, fields):
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("ReferenceDataRequest")
        set_tickers(request, tickers)
        set_fields(request, fields)

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
                        key = element.getElement(0).name().__str__()
                        value = element.getElementAsString(key)
                        elements.append(value)

        return elements
