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
import datetime
from unittest import TestCase

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from tests.unit_tests.config.test_settings import get_test_settings


class TestBloombergValueParser(TestCase):

    def setUp(self) -> None:
        self.ticker = BloombergTicker("EUITEMUM Index")

        try:
            settings = get_test_settings()
            self.bbg_provider = BloombergDataProvider(settings)
            self.bbg_provider.connect()

        except Exception as e:
            raise self.skipTest(e)

    def test_get_string_values(self):
        field = "OBSERVATION_PERIOD"
        result = self.bbg_provider.get_current_values(self.ticker, field)
        self.assertIsInstance(result, str)

    def test_get_float_values(self):
        field = "PX_Last"
        result = self.bbg_provider.get_current_values(self.ticker, field)
        self.assertIsInstance(result, float)

    def test_get_date_values(self):
        field = "ECO_RELEASE_DT"
        result = self.bbg_provider.get_current_values(self.ticker, field)
        self.assertIsInstance(result, datetime.datetime)

    def test_get_time_values(self):
        field = "ECO_RELEASE_TIME"
        result = self.bbg_provider.get_current_values(self.ticker, field)
        self.assertIsInstance(result, datetime.time)

    def test_get_none_values(self):
        field = "BN_SURVEY_MEDIAN"
        result = self.bbg_provider.get_current_values(self.ticker, field)
        self.assertIsNone(result)
