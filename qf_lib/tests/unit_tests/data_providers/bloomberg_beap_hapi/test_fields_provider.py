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

from unittest.mock import Mock, PropertyMock
import unittest

from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_fields_provider import BloombergBeapHapiFieldsProvider
from urllib.parse import urljoin


class TestBloombergBeapHapiFieldsProvider(unittest.TestCase):

    def setUp(self):
        self.session_mock = Mock()
        self.post_response = Mock()
        self.session_mock.post.return_value = self.post_response
        self.address_url = '/eap/catalogs/address_url_id/'
        self.fieldlist_id = 'sOmwhEReOveRTHeRainBOW'
        self.location = '{}fieldLists/{}/'.format(self.address_url, self.fieldlist_id)
        self.post_response.headers = {'Location': self.location}
        self.host = 'https://api.bloomberg.com'
        self.account_url = urljoin(self.host, self.address_url)
        self.fields = ['PX_LAST']

    def test_get_fields_url__get_response(self):
        self.session_mock.get.return_value.status_code = 200
        self.session_mock.get.return_value.json.return_value.get.return_value = [{'mnemonic': 'PX_LAST', 'type': 'Price'}]
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        url, field_list_to_type = provider.get_fields_url(self.fieldlist_id, self.fields)
        self.assertEqual(url, urljoin(self.host, self.location))
        self.assertEqual(field_list_to_type, {'PX_LAST': 'Price'})

    def test_get_fields_url__post_response(self):
        response = Mock()
        type(response).status_code = PropertyMock(side_effect=[404, 200])
        self.session_mock.get.return_value = response
        self.post_response.status_code = 201
        self.post_response.json.return_value.get.return_value = [{'mnemonic': 'PX_LAST', 'type': 'Price'}]
        self.session_mock.get.return_value.json.return_value.get.return_value = [{'mnemonic': 'PX_LAST', 'type': 'Price'}]
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        url, field_list_to_type = provider.get_fields_url(self.fieldlist_id, self.fields)
        self.assertEqual(url, urljoin(self.host, self.location))
        self.assertEqual(field_list_to_type, {'PX_LAST': 'Price'})

    def test_get_fields_url__unknown_get_response(self):
        self.session_mock.get.return_value.status_code = 404
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        self.assertRaises(BloombergError, provider.get_fields_url, self.fieldlist_id, self.fields)

    def test_get_fields_url__unknown_post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 200
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        self.assertRaises(BloombergError, provider.get_fields_url, self.fieldlist_id, self.fields)

    def test_get_fields_history_url__get_response(self):
        self.session_mock.get.return_value.status_code = 200
        self.session_mock.get.return_value.json.return_value.get.return_value = [{'mnemonic': 'PX_LAST', 'type': 'Price'}]
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        url, field_list_to_type = provider.get_fields_history_url(self.fieldlist_id, self.fields)
        self.assertEqual(url, urljoin(self.host, self.location))
        self.assertEqual(field_list_to_type, {'PX_LAST': 'Price'})

    def test_get_fields_history_url__post_response(self):
        response = Mock()
        type(response).status_code = PropertyMock(side_effect=[404, 200])
        self.session_mock.get.return_value = response
        self.post_response.status_code = 201
        self.post_response.json.return_value.get.return_value = [{'mnemonic': 'PX_LAST', 'type': 'Price'}]
        self.session_mock.get.return_value.json.return_value.get.return_value = [{'mnemonic': 'PX_LAST', 'type': 'Price'}]
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        url, field_list_to_type = provider.get_fields_history_url(self.fieldlist_id, self.fields)
        self.assertEqual(url, urljoin(self.host, self.location))
        self.assertEqual(field_list_to_type, {'PX_LAST': 'Price'})

    def test_get_fields_history_url__unknown_get_response(self):
        self.session_mock.get.return_value.status_code = 404
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        self.assertRaises(BloombergError, provider.get_fields_history_url, self.fieldlist_id, self.fields)

    def test_get_fields_history_url__unknown_post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 200
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        self.assertRaises(BloombergError, provider.get_fields_history_url, self.fieldlist_id, self.fields)
