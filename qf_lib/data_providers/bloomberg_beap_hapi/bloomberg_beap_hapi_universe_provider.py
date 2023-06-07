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
from typing import Union, Sequence, Optional, List, Tuple
import pprint
from urllib.parse import urljoin
import requests
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.data_providers.bloomberg.exceptions import BloombergError


class BloombergBeapHapiUniverseProvider:
    """
    Class to prepare and create universe for Bloomberg HAPI

    Parameters
    ----------
    host: str
        The host address e.g. 'https://api.bloomberg.com'
    session: requests.Session
        The session object
    account_url: str
        The URL of hapi account
    """

    def __init__(self, host: str, session: requests.Session, account_url: str):
        self.host = host
        self.session = session
        self.account_url = account_url
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_universe_url(self, universe_id: str, tickers: Union[str, Sequence[str]],
                         fields_overrides: Optional[List[Tuple]] = None) -> str:
        """
        Method to create hapi universe and get universe address URL

        Parameters
        ----------
        universe_id: str
            ID of the hapi universe
        tickers: Union[str, Sequence[str]]
            Ticker str, list of tickers str
        fields_overrides: Optional[List[Tuple]]
            list of tuples representing overrides, where first element is always the name of the override and second
            element is the value e.g. in case if we want to download 'FUT_CHAIN' and include expired
            contracts we add the following overrides [('INCLUDE_EXPIRED_CONTRACTS', 'Y'),]

        Returns
        -------
        universe_url
            URL address of created hapi universe
        """
        tickers, got_single_field = convert_to_list(tickers, str)
        tickers_and_types = [self._get_identifier_and_type(ticker) for ticker in tickers]
        contains = [{'@type': 'Identifier', 'identifierType': identifier_type, 'identifierValue': identifier}
                    for identifier_type, identifier in tickers_and_types if identifier]
        if len(contains) == 0:
            raise ValueError("No valid identifiers (tickers) were provided. Please refer to the logs and adjust your "
                             "data request accordingly.")

        if fields_overrides:
            # noinspection PyTypeChecker
            contains[0]['fieldOverrides'] = [{
                '@type': 'FieldOverride',
                'mnemonic': key,
                'override': value
            } for key, value in fields_overrides
            ]
        universe_payload = {
            '@type': 'Universe',
            'identifier': universe_id,
            'title': 'Universe Payload',
            'description': 'Universe Payload used in creating fields component',
            'contains': contains
        }

        self.logger.info('Universe component payload:\n:%s', pprint.pformat(universe_payload))
        universe_url = urljoin(self.account_url, 'universes/{}/'.format(universe_id))

        # check if already exists, if not then post
        response = self.session.get(universe_url)

        if response.status_code != 200:
            universe_url = urljoin(self.account_url, 'universes/')
            response = self.session.post(universe_url, json=universe_payload)

            # Check it went well and extract the URL of the created universe
            if response.status_code != requests.codes.created:
                self.logger.error('Unexpected response status code: %s', response.status_code)
                raise BloombergError('Unexpected response')

            universe_location = response.headers['Location']
            universe_url = urljoin(self.host, universe_location)
            self.logger.info('Universe successfully created at %s', universe_url)

        return universe_url

    def _get_identifier_and_type(self, identifier: str) -> Tuple[Optional[str], Optional[str]]:
        blp_hapi_compatibility_mapping = {
            "ticker": "TICKER",
            "cusip": "CUSIP",
            "buid": "BB_UNIQUE",
            "bbgid": "BB_GLOBAL",
            "isin": "ISIN",
            "wpk": "WPK",
            "sedol1": "SEDOL",
            "common": "COMMON_NUMBER",
            "cins": "CINS",
            "cats": "CATS"
        }

        identifier = f"/ticker/{identifier}" if not identifier.startswith("/") else identifier
        match = re.match(r"^/(\w+)/(.+)", identifier)
        if not match:
            self.logger.error(f"Detected incorrect identifier: {identifier}. It will be removed from the data request.\n"
                              f"In order to provide an identifier, which is not a ticker, please use "
                              f"'/id_type/identifier' format, with id_type being one of the following: "
                              f"{blp_hapi_compatibility_mapping.values()}")
            return None, None

        id_type, id = match.groups()
        try:
            return blp_hapi_compatibility_mapping[id_type.lower()], id
        except KeyError:
            self.logger.error(
                f"Detected incorrect identifier type: {id_type.lower()}. The identifier will be removed from the "
                f"data request.\n"
                f"List of valid identifier types: {blp_hapi_compatibility_mapping.values()}")
            return None, None
