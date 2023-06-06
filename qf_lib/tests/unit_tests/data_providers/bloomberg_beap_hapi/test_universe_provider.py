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
from unittest.mock import Mock
import unittest
from urllib.parse import urljoin

from qf_lib.data_providers.bloomberg.exceptions import BloombergError
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_universe_provider import BloombergBeapHapiUniverseProvider


class TestBloombergBeapHapiUniverseProvider(unittest.TestCase):

    def setUp(self):
        self.session_mock = Mock()
        self.post_response = Mock()
        self.session_mock.post.return_value = self.post_response
        self.address_url = '/eap/catalogs/address_url_id/'
        self.fieldlist_id = 'sOmwhEReOveRTHeRainBOW'
        self.location = '{}universes/{}/'.format(self.address_url, self.fieldlist_id)
        self.host = 'https://api.bloomberg.com'
        self.account_url = urljoin(self.host, self.address_url)
        self.post_response.headers = {'Location': self.location}

    def test_get_universe_url__get_response(self):
        self.session_mock.get.return_value.status_code = 200
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        field_overrides = [("CHAIN_DATE", datetime.now().strftime('%Y%m%d')), ('INCLUDE_EXPIRED_CONTRACTS', 'Y')]
        tickers = ["SPY US Equity"]
        url = provider.get_universe_url(self.fieldlist_id, tickers, field_overrides)
        self.assertEqual(url, urljoin(self.host, self.location))

    def test_get_universe_url__post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 201
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        field_overrides = [("CHAIN_DATE", datetime.now().strftime('%Y%m%d')), ('INCLUDE_EXPIRED_CONTRACTS', 'Y')]
        tickers = ["SPY US Equity"]
        url = provider.get_universe_url(self.fieldlist_id, tickers, field_overrides)
        self.assertEqual(url, urljoin(self.host, self.location))

    def test_get_universe_url__unknown_get_response(self):
        self.session_mock.get.return_value.status_code = 404
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        field_overrides = [("CHAIN_DATE", datetime.now().strftime('%Y%m%d')), ('INCLUDE_EXPIRED_CONTRACTS', 'Y')]
        tickers = ["SPY US Equity"]
        self.assertRaises(BloombergError, provider.get_universe_url, self.fieldlist_id, tickers, field_overrides)

    def test_get_universe_url__unknown_post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 200
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        field_overrides = [("CHAIN_DATE", datetime.now().strftime('%Y%m%d')), ('INCLUDE_EXPIRED_CONTRACTS', 'Y')]
        tickers = ["SPY US Equity"]
        self.assertRaises(BloombergError, provider.get_universe_url, self.fieldlist_id, tickers, field_overrides)

    def test_get_universe_url__no_correct_identifiers(self):
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        tickers = ["/incorrect_type/SPY US Equity"]
        self.assertRaises(ValueError, provider.get_universe_url, self.fieldlist_id, tickers)

    def test_get_universe_url__empty_identifiers_list(self):
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        tickers = []
        self.assertRaises(ValueError, provider.get_universe_url, self.fieldlist_id, tickers)

    def test_get_universe_url__correct_identifier_with_special_characters(self):
        self.session_mock.get.return_value.status_code = 200
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        tickers = ["/ticker/AA/ US Equity"]
        url = provider.get_universe_url(self.fieldlist_id, tickers)
        self.assertEqual(url, urljoin(self.host, self.location))

    def test_get_universe_url__correct_ticker_with_special_characters(self):
        self.session_mock.get.return_value.status_code = 200
        provider = BloombergBeapHapiUniverseProvider(self.host, self.session_mock, self.account_url)
        tickers = ["AA/ US Equity"]
        url = provider.get_universe_url(self.fieldlist_id, tickers)
        self.assertEqual(url, urljoin(self.host, self.location))
