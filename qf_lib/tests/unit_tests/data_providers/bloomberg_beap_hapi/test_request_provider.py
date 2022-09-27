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

from unittest.mock import Mock
import unittest
from urllib.parse import urljoin

from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_request_provider import BloombergBeapHapiRequestsProvider


class TestBloombergBeapHapiRequestProvider(unittest.TestCase):

    def setUp(self):
        self.session_mock = Mock()
        self.post_response = Mock()
        self.session_mock.post.return_value = self.post_response
        self.address_url = '/eap/catalogs/address_url_id/'
        self.request_id = 'sOmwhEReOveRTHeRainBOW'
        self.host = 'https://api.bloomberg.com'
        self.account_url = urljoin(self.host, self.address_url)
        self.trigger_url = urljoin(self.host, '{}triggers/ctaAdhocTrigger/'.format(self.address_url))

    def test_create_request__unknown_get_response(self):
        self.session_mock.get.return_value.status_code = 404
        provider = BloombergBeapHapiRequestsProvider(self.host, self.session_mock, self.account_url, self.trigger_url)
        self.assertRaises(BloombergError, provider.create_request, self.request_id, 'some_universe_url', 'some_field_list_url')

    def test_create_request__unknown_post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 200
        provider = BloombergBeapHapiRequestsProvider(self.host, self.session_mock, self.account_url, self.trigger_url)
        self.assertRaises(BloombergError, provider.create_request, self.request_id, 'some_universe_url', 'some_field_list_url')
