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
from typing import Union, Sequence, Tuple, Dict
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

    def get_fields_url(self, fields_list_id: str, fields: Union[str, Sequence[str]]) -> Tuple[str, Dict]:
        """
        Method to create hapi fields and get fields address URL

        Parameters
        ----------
        fields_list_id: str
            ID of created hapi fields
        fields: str
            Fields used in query

        Returns
        -------
        Tuple[str, Dict]
            URL address of created fields
            dictionary mapping requested, correct fields into their corresponding types
        """
        fields, got_single_field = convert_to_list(fields, str)
        cont = [{'mnemonic': field} for field in fields]

        fields_list_payload = {
            '@type': 'DataFieldList',
            'identifier': fields_list_id,
            'title': 'FieldList Payload',
            'description': 'FieldList Payload used in creating fields component',
            'contains': cont
        }

        self.logger.info('Field list component payload:\n %s', pprint.pformat(fields_list_payload))
        return self._get_fields_list_common(fields_list_id, fields_list_payload)

    def get_fields_history_url(self, fields_list_id: str, fields: Union[str, Sequence[str]]) -> Tuple[str, Dict]:
        """
        Method to create history hapi fields and get history fields address URL

        Parameters
        ----------
        fields_list_id: str
            ID of hapi fields
        fields: str
            History fields used in query

        Returns
        -------
        Tuple[str, Dict]
            URL address of created fields
            dictionary mapping requested, correct fields into their corresponding types
        """
        fields, got_single_field = convert_to_list(fields, str)
        cont = [{'mnemonic': field} for field in fields]

        fields_list_payload = {
            '@type': 'HistoryFieldList',
            'identifier': fields_list_id,
            'title': 'FieldList History Payload',
            'description': 'FieldList History Payload used in creating fields component',
            'contains': cont
        }
        self.logger.info('Field list component payload:\n %s', pprint.pformat(fields_list_payload))
        return self._get_fields_list_common(fields_list_id, fields_list_payload)

    def _get_fields_list_common(self, fields_list_id, fields_list_payload) -> Tuple[str, Dict]:
        fields_list_url = urljoin(self.account_url, f'fieldLists/{fields_list_id}/')

        # check if already exists, if not then post
        response = self.session.get(fields_list_url)
        if response.status_code != 200:
            fields_list_url = urljoin(self.account_url, 'fieldLists/')
            response = self.session.post(fields_list_url, json=fields_list_payload)

            # Check it went well and extract the URL of the created field list
            if response.status_code != requests.codes.created:
                raise BloombergError(f'Unexpected response status code {response.status_code}')

            fields_list_location = response.headers['Location']
            fields_list_url = urljoin(self.host, fields_list_location)
            self.logger.info('Field list successfully created at %s', fields_list_url)

            response = self.session.get(fields_list_url)
            if response.status_code != 200:
                raise BloombergError('Could not retrieve the fields list url')

        field_to_type = {
            fields_data['mnemonic']: fields_data['type']
            for fields_data in response.json().get('contains')
        }

        return fields_list_url, field_to_type
