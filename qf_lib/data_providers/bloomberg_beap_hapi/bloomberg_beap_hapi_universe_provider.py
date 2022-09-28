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
        contains = [{'@type': 'Identifier', 'identifierType': 'TICKER', 'identifierValue': ticker} for ticker in
                    tickers]
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
