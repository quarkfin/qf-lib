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
from typing import Union, Sequence
import pprint
from urllib.parse import urljoin
import requests
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.data_providers.bloomberg.exceptions import BloombergError


class BloombergBeapHapiFieldsProvider:
    """
    Class to prepare and create fields for Bloomberg HAPI

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

    def get_fields_url(self, fieldlist_id: str, fields: Union[str, Sequence[str]]) -> str:
        """
        Method to create hapi fields and get fields address URL

        Parameters
        ----------
        fieldlist_id: str
            ID of created hapi fields
        fields: str
            Fields used in query

        Returns
        -------
        fieldlist_url: str
            URL address of created hapi fields
        """
        fields, got_single_field = convert_to_list(fields, str)
        cont = [{'mnemonic': field} for field in fields]

        fieldlist_payload = {
            '@type': 'DataFieldList',
            'identifier': fieldlist_id,
            'title': 'FieldList Payload',
            'description': 'FieldList Payload used in creating fields component',
            'contains': cont
        }

        self.logger.info('Field list component payload:\n %s', pprint.pformat(fieldlist_payload))
        fieldlist_url = self._get_fields_list_common(fieldlist_id, fieldlist_payload)
        return fieldlist_url

    def get_fields_history_url(self, fieldlist_id: str, fields: Union[str, Sequence[str]]) -> str:
        """
        Method to create history hapi fields and get history fields address URL

        Parameters
        ----------
        fieldlist_id: str
            ID of hapi fields
        fields: str
            History fields used in query

        Returns
        -------
        fieldlist_url: str
            URL address of created hapi fields
        """
        fields, got_single_field = convert_to_list(fields, str)
        cont = [{'mnemonic': field} for field in fields]

        fieldlist_payload = {
            '@type': 'HistoryFieldList',
            'identifier': fieldlist_id,
            'title': 'FieldList History Payload',
            'description': 'FieldList History Payload used in creating fields component',
            'contains': cont
        }
        self.logger.info('Field list component payload:\n %s', pprint.pformat(fieldlist_payload))
        fieldlist_url = self._get_fields_list_common(fieldlist_id, fieldlist_payload)
        return fieldlist_url

    def _get_fields_list_common(self, fieldlist_id, fieldlist_payload) -> str:
        fieldlist_url = urljoin(self.account_url, 'fieldLists/{}/'.format(fieldlist_id))

        # check if already exists, if not then post
        response = self.session.get(fieldlist_url)

        if response.status_code != 200:
            fieldlist_url = urljoin(self.account_url, 'fieldLists/')
            response = self.session.post(fieldlist_url, json=fieldlist_payload)

            # Check it went well and extract the URL of the created field list
            if response.status_code != requests.codes.created:
                self.logger.error('Unexpected response status code: %s', response.status_code)
                raise BloombergError('Unexpected response')

            fieldlist_location = response.headers['Location']
            fieldlist_url = urljoin(self.host, fieldlist_location)
            self.logger.info('Field list successfully created at %s', fieldlist_url)

        return fieldlist_url
