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
import re
from datetime import datetime
from typing import Sequence, Dict, List

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.data_providers.bloomberg.bloomberg_names import REF_DATA_SERVICE_URI, SECURITY, FIELD_DATA, FUT_CHAIN
from qf_lib.data_providers.bloomberg.helpers import set_tickers, set_fields, get_response_events, \
    check_event_for_errors, extract_security_data, convert_to_bloomberg_date, \
    FIELD_EXCEPTIONS, SECURITY_ERROR


class FuturesDataProvider(object):

    def __init__(self, session):
        self._session = session
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_list_of_tickers_in_the_future_chain(self, tickers: Sequence[BloombergFutureTicker]) \
            -> Dict[BloombergFutureTicker, List[BloombergTicker]]:
        """
        For given list of BloombergFutureTickers returns a dictionary mapping each BloombergFutureTicker into a list
        of BloombergTickers, which belong to its futures chain.
        """

        # For each of the BloombergFutureTickers generate a specific random ticker, which may be further used to
        # download the list of all specific tickers belonging to the chain, e.g. for Cotton future tickers family,
        # one needs a specific ticker belonging to this family (e.g. BloombergTicker("CTZ9 Comdty")), which is used
        # in the request.
        random_ticker_string_to_future_ticker = {
            future_ticker.get_random_specific_ticker().ticker: future_ticker for future_ticker in tickers
        }

        # Define mapping functions from strings into BloombergFutureTickers and BloombergTickers
        def future_ticker_from_string(specific_random_string: str) -> BloombergFutureTicker:
            return random_ticker_string_to_future_ticker[specific_random_string]

        def tickers_from_strings(tickers_strings: List[str]) -> List[BloombergTicker]:
            return [BloombergTicker.from_string(ticker) for ticker in tickers_strings]

        all_future_tickers_str_to_chain_tickers_list = {}

        # Set used to keep track of all specific, random tickers that were already used to fetch the futures chains for
        # certain future tickers.
        fetched_tickers_set = set()

        # Create a list of all specific tickers strings
        specific_tickers_strings_to_fetch = list(random_ticker_string_to_future_ticker.keys())

        while specific_tickers_strings_to_fetch:
            # Create and send the request
            self._create_and_send_request(specific_tickers_strings_to_fetch)

            # Return dictionary mapping the tickers to lists of futures chains tickers (contains only these tickers,
            # for which correct random tickers were provided)
            future_ticker_str_to_chain_tickers_list = {
                key: value for key, value in
                self._receive_futures_response(random_ticker_string_to_future_ticker).items() if value
            }

            # Update the main dictionary which maps future tickers string into their future chains
            all_future_tickers_str_to_chain_tickers_list.update(future_ticker_str_to_chain_tickers_list)
            # Update the set of all fetched tickers
            fetched_tickers_set.update(specific_tickers_strings_to_fetch)

            # Compute which tickers were not fetched correctly (in order to retry downloading the futures chains)
            invalid_random_tickers_strings = set(specific_tickers_strings_to_fetch).difference(
                all_future_tickers_str_to_chain_tickers_list.keys()
            )
            # Get list of BloombergFutureTickers for which the futures chains were not fetched
            future_tickers_not_fetched = [future_ticker_from_string(t) for t in invalid_random_tickers_strings]

            # Generate new random specific tickers in order to substitute the previous specific random tickers
            # with them and correctly download the futures chains
            specific_tickers_strings_to_fetch_dict = {fut_ticker.get_random_specific_ticker().ticker: fut_ticker
                                                      for fut_ticker in future_tickers_not_fetched}
            # Update the dictionary mapping the random specific tickers to future tickers with the newly generated
            # tickers
            random_ticker_string_to_future_ticker.update(specific_tickers_strings_to_fetch_dict)

            # Create the list of specific tickers that need to be fetched within the next loop iteration
            specific_tickers_strings_to_fetch = list(specific_tickers_strings_to_fetch_dict.keys())
            # Filter out these random specific tickers, that were already used at least once to download the chains
            specific_tickers_strings_to_fetch = [ticker for ticker in specific_tickers_strings_to_fetch
                                                 if ticker not in fetched_tickers_set]

        # Create a dictionary, which is mapping BloombergFutureTickers to lists of BloombergTickers belonging to
        # corresponding futures chains (map all of the strings from future_ticker_to_chain_tickers_list dictionary
        # into BoombergTickers and BloombergFutureTickers)
        future_ticker_str_to_chain_tickers_list = {
            future_ticker_from_string(future_ticker_str): tickers_from_strings(specific_tickers_strings_list)
            for future_ticker_str, specific_tickers_strings_list in all_future_tickers_str_to_chain_tickers_list.items()
        }

        # Check if for all of the requested tickers the futures chains were returned, and if not - raise BloombergError
        lacking_tickers = set(tickers).difference(future_ticker_str_to_chain_tickers_list.keys())

        if lacking_tickers:
            lacking_tickers_str = [t.name for t in lacking_tickers]
            error_message = "The requested futures chains for the BloombergFutureTickers {} could not have been " \
                            "downloaded successfully".format(lacking_tickers_str)
            self.logger.error(error_message)

        return future_ticker_str_to_chain_tickers_list

    def _create_and_send_request(self, tickers):
        ref_data_service = self._session.getService(REF_DATA_SERVICE_URI)
        request = ref_data_service.createRequest("ReferenceDataRequest")

        set_tickers(request, tickers, )
        set_fields(request, ["FUT_CHAIN"])

        # Set the parameters to include all the future contracts, that already expired
        override_names = ("CHAIN_DATE", "INCLUDE_EXPIRED_CONTRACTS")
        override_values = (convert_to_bloomberg_date(datetime.now()), "Y")

        override_fields = ("fieldId", "value")
        self._set_overrides(request, override_fields, override_names, override_values)

        self._session.sendRequest(request)

    def _set_overrides(self, request, override_fields, override_names, override_values):
        overrides = request.getElement("overrides")

        for parameters in zip(override_names, override_values):
            override = overrides.appendElement()
            for field, value in zip(override_fields, parameters):
                override.setElement(field, value)

    def _receive_futures_response(self, random_ticker_string_to_future_ticker: Dict[str, BloombergFutureTicker]):
        response_events = get_response_events(self._session)
        ticker_to_futures_chain = {}

        def data_is_correct(data):
            if data.hasElement(SECURITY_ERROR):
                return False
            if security_data.hasElement(FIELD_EXCEPTIONS):
                field_exceptions = data.getElement(FIELD_EXCEPTIONS)
                if field_exceptions.numValues() > 0:
                    return False
            return True

        for event in response_events:
            check_event_for_errors(event)
            security_data_array = extract_security_data(event)

            for i in range(security_data_array.numValues()):

                security_data = security_data_array.getValueAsElement(i)

                if data_is_correct(security_data):
                    security_name = security_data.getElementAsString(SECURITY)
                    family_id_template = random_ticker_string_to_future_ticker[security_name].family_id
                    # Family id are in the following form: CT{} Comdty -> {} should be replaced with a correct month
                    # code
                    regex_template = family_id_template.replace("{}", "[A-Z][0-9]{1,2}")

                    future_chain_array = security_data.getElement(FIELD_DATA).getElement(FUT_CHAIN)
                    ticker_to_futures_chain[security_name] = []

                    for j in range(future_chain_array.numValues()):
                        future_ticker = future_chain_array.getValueAsElement(j)
                        ticker_value = future_ticker.getElementAsString("Security Description")
                        if re.match(regex_template, ticker_value):
                            ticker_to_futures_chain[security_name].append(ticker_value)

        return ticker_to_futures_chain
