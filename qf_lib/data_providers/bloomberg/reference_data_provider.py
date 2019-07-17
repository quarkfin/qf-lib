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
