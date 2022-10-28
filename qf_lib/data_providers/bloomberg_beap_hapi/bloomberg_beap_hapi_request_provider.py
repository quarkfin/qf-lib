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
import pprint
from typing import Dict, Optional
from urllib.parse import urljoin
import requests
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.bloomberg.exceptions import BloombergError


class BloombergBeapHapiRequestsProvider:
    """
    Class to prepare and create requests for Bloomberg HAPI

    Parameters
    ----------
    host: str
        The host address e.g. 'https://api.bloomberg.com'
    session: requests.Session
        The session object
    account_url: str
        The URL of hapi account
    trigger_url: str
        The URL of hapi trigger
    terminal_identity_user: Optional[str]
        parameter to link the Data License to a Bloomberg Anywhere or Bloomberg Professional account.
        The User value can be obtained by running IAM <GO> in the Bloomberg terminal. In case of Bloomberg Anywhere only
        this parameter should be used, while in case of Bloomberg Professional the S/N parameter is additionally required.
    terminal_identity_sn: Optional[str]
        parameter to link the Data License to a Bloomberg Professional account. The S/N value can be obtained by
        running IAM <GO> in the Bloomberg terminal (the whole value should be passed as a string, e.g. 12345-678)
    """

    def __init__(self, host: str, session: requests.Session, account_url: str, trigger_url: str,
                 terminal_identity_user: Optional[str] = None, terminal_identity_sn: Optional[str] = None):
        self.host = host
        self.session = session
        self.account_url = account_url
        self.trigger_url = trigger_url
        self._terminal_identity_user = self._parse_terminal_identity_user(terminal_identity_user)
        self._terminal_identity_sn = self._parse_terminal_identity_sn(terminal_identity_sn)

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def create_request(self, request_id: str, universe_url: str, fieldlist_url: str):
        """
        Method to create hapi request and get request address URL

        Parameters
        ----------
        request_id: str
            ID of request
        universe_url: str
            URL address of the universe
        fieldlist_url: str
            URL address of the fields
        """
        request_payload = {
            '@type': 'DataRequest',
            'identifier': request_id,
            'title': 'Request Payload',
            'description': 'Request Payload used in creating fields component',
            'universe': universe_url,
            'fieldList': fieldlist_url,
            'trigger': self.trigger_url,
            'formatting': {
                '@type': 'DataFormat',
                'columnHeader': True,
                'dateFormat': 'yyyymmdd',
                'delimiter': '|',
                'fileType': 'unixFileType',
                'outputFormat': 'variableOutputFormat',
            },
            'pricingSourceOptions': {
                '@type': 'DataPricingSourceOptions',
                'prefer': {'mnemonic': 'BGN'}
            }
        }

        self._set_terminal_identity(request_payload)
        self.logger.info('Request component payload:\n%s', pprint.pformat(request_payload))
        self._create_request_common(request_id, request_payload)

    def create_request_history(self, request_id: str, universe_url: str, fieldlist_url: str, start_date: datetime,
                               end_date: datetime, frequency: Frequency, currency: Optional[str] = None):
        """
        Method to create hapi history request

        Parameters
        ----------
        request_id: str
            ID of request
        universe_url: str
            URL address of the universe
        fieldlist_url: str
            URL address of the fields
        start_date: datetime
            Start of the history data
        end_date: datetime
            End of the history data
        frequency: Frequency
            Frequency of data
        currency: Optional[str]
            currency which should be used to make the requests
        """
        request_payload = {
            '@type': 'HistoryRequest',
            'identifier': request_id,
            'title': 'Request History Payload',
            'description': 'Request History Payload used in creating fields component',
            'universe': universe_url,
            'fieldList': fieldlist_url,
            'trigger': self.trigger_url,
            'formatting': {
                '@type': 'HistoryFormat',
                'dateFormat': 'yyyymmdd',
                'fileType': 'unixFileType',
                'displayPricingSource': True,
            },
            'runtimeOptions': {
                '@type': 'HistoryRuntimeOptions',
                'period': str(frequency).lower(),
                'dateRange': {
                    '@type': 'IntervalDateRange',
                    'startDate': date_to_str(start_date),
                    'endDate': date_to_str(end_date)
                }
            },
            'pricingSourceOptions': {
                '@type': 'HistoryPricingSourceOptions',
                'exclusive': True
            }
        }

        if currency:
            request_payload['runtimeOptions']['historyPriceCurrency'] = currency
        self._set_terminal_identity(request_payload)
        self.logger.info('Request history component payload:\n%s', pprint.pformat(request_payload))
        self._create_request_common(request_id, request_payload)

    def _create_request_common(self, request_id: str, request_payload: Dict):
        request_url = urljoin(self.account_url, 'requests/{}/'.format(request_id))

        # check if already exists, if not then post
        response = self.session.get(request_url)

        if response.status_code != 200:
            request_url = urljoin(self.account_url, 'requests/')
            response = self.session.post(request_url, json=request_payload)

            # Check it went well and extract the URL of the created request
            if response.status_code != requests.codes.created:
                self.logger.error('Unexpected response status code: %s', response.status_code)
                raise BloombergError('Unexpected response')

            request_location = response.headers['Location']
            request_url = urljoin(self.host, request_location)
            self.logger.info('%s resource has been successfully created at %s', request_id, request_url)

    def _set_terminal_identity(self, request_payload: Dict):
        if self._terminal_identity_sn and self._terminal_identity_user:
            request_payload["terminalIdentity"] = {
              "@type": "BlpTerminalIdentity",
              "userNumber": self._terminal_identity_user,
              "serialNumber": self._terminal_identity_sn[0],
              "workStation": self._terminal_identity_sn[1]
            }
        elif self._terminal_identity_user:
            request_payload["terminalIdentity"] = {
                "@type": "BbaTerminalIdentity",
                "userNumber": self._terminal_identity_user,
            }

    @staticmethod
    def _parse_terminal_identity_user(terminal_identity_user: str):
        try:
            return int(terminal_identity_user) if terminal_identity_user is not None else terminal_identity_user
        except ValueError:
            raise ValueError(f"Incorrect terminal user provided: {terminal_identity_user}. "
                             f"The User value can be obtained by running IAM <GO> in the Bloomberg terminal.")

    @staticmethod
    def _parse_terminal_identity_sn(terminal_identity_sn: str):
        try:
            return [int(i) for i in terminal_identity_sn.split("-")] if terminal_identity_sn is not None \
                else terminal_identity_sn
        except ValueError:
            raise ValueError(f"Incorrect terminal S/N provided: {terminal_identity_sn}. "
                             f"The S/N value can be obtained by running IAM <GO> in the Bloomberg terminal.")
