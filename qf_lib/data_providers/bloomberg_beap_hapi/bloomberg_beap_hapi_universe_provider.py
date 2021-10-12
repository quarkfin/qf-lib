from typing import Union, Sequence
import pprint
from urllib.parse import urljoin
import requests
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from datetime import datetime

from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg.helpers import convert_to_bloomberg_date


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

    def get_universe_url(self, universe_id: str, tickers: Union[dict, str, Sequence[str]], fieldsOverrides: bool) -> str:
        """
        Method to create hapi universe and get universe address URL

        Parameters
        ----------
        universe_id: str
            ID of the hapi universe
        contains: Union[dict, str, Sequence[str]]
            Ticker str, list of tickers str or dict
        fieldsOverrides: bool
            If True, it uses fieldsOvverides
        Returns
        -------
        universe_url
            URL address of created hapi universe
        """
        if not isinstance(tickers, dict):
            tickers, got_single_field = convert_to_list(tickers, str)
        contains = [{'@type': 'Identifier', 'identifierType': 'TICKER', 'identifierValue': ticker} for ticker in tickers]
        if fieldsOverrides:
            # noinspection PyTypeChecker
            contains[0]['fieldOverrides'] = [
                {
                    '@type': 'FieldOverride',
                    'mnemonic': "CHAIN_DATE",
                    'override': convert_to_bloomberg_date(datetime.now())
                },
                {
                    '@type': 'FieldOverride',
                    'mnemonic': "INCLUDE_EXPIRED_CONTRACTS",
                    'override': "Y"
                }
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
