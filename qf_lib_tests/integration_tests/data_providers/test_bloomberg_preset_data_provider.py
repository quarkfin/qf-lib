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
import unittest

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib_tests.integration_tests.data_providers.test_bloomberg_intraday import TestBloombergIntraday
from qf_lib_tests.unit_tests.config.test_settings import get_test_settings

settings = get_test_settings()
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestBloombergPreset(TestBloombergIntraday):
    """
    Test case responsible for testing the Preset Data Provider. On the set up the test case loads the data from
    Bloomberg with 1 minute frequency and with 15 minutes frequency. This data is used to create two preset data
    providers.
    """

    def setUp(self):
        self.FREQUENCY = Frequency.MIN_15

        self.START_DATE = str_to_date('2019-06-20 12:09:00.0', DateFormat.FULL_ISO)
        self.END_DATE = str_to_date('2019-06-20 15:01:00.0', DateFormat.FULL_ISO)

        self.preset_provider = bbg_provider
        self.preset_price_provider_lower_frequency = self.price_provider
        self.preset_history_provider_lower_frequency = self.history_provider

    def test_price_single_ticker_single_field_intraday(self):
        # single ticker, single field
        data = self.preset_provider.get_price(tickers=self.SINGLE_TICKER, fields=self.SINGLE_PRICE_FIELD,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=self.FREQUENCY)

        data2 = self.preset_price_provider_lower_frequency.get_price(tickers=self.SINGLE_TICKER,
                                                                     fields=self.SINGLE_PRICE_FIELD,
                                                                     start_date=self.START_DATE,
                                                                     end_date=self.END_DATE,
                                                                     frequency=self.FREQUENCY)
        self.assertTrue(data.equals(data2))

    def test_price_multiple_tickers_multiple_fields_intraday(self):
        # testing for single date
        data = self.preset_provider.get_price(tickers=self.MANY_TICKERS, fields=self.MANY_PRICE_FIELDS,
                                              start_date=self.START_DATE, end_date=self.END_DATE,
                                              frequency=self.FREQUENCY)

        data2 = self.preset_price_provider_lower_frequency.get_price(tickers=self.MANY_TICKERS,
                                                                     fields=self.MANY_PRICE_FIELDS,
                                                                     start_date=self.START_DATE,
                                                                     end_date=self.END_DATE,
                                                                     frequency=self.FREQUENCY)

        self.assertTrue(data.equals(data2))


if __name__ == '__main__':
    unittest.main()
