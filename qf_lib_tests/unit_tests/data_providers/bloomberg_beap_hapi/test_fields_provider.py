from unittest.mock import Mock
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
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        url = provider.get_fields_url(self.fieldlist_id, self.fields)
        self.assertEqual(url, urljoin(self.host, self.location))

    def test_get_fields_url__post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 201
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        url = provider.get_fields_url(self.fieldlist_id, self.fields)
        self.assertEqual(url, urljoin(self.host, self.location))

    def test_get_fields_url__unknown_get_response(self):
        self.session_mock.get.return_value.status_code = 404
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        self.assertRaises(BloombergError, provider.get_fields_url, self.fieldlist_id, self.fields)

    def test_get_fields_url__unknown_post_response(self):
        self.session_mock.get.return_value.status_code = 404
        self.post_response.status_code = 200
        provider = BloombergBeapHapiFieldsProvider(self.host, self.session_mock, self.account_url)
        self.assertRaises(BloombergError, provider.get_fields_url, self.fieldlist_id, self.fields)
