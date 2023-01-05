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
from io import BytesIO
from textwrap import dedent
from unittest.mock import patch, Mock

from numpy import datetime64, datetime_as_string, float64, nan
from pandas import isna
from pandas._testing import assert_frame_equal

from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser import BloombergBeapHapiParser


class TestBloombergBeapHapiParser(unittest.TestCase):

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_history_single_ticker_single_field_multiple_dates(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            PX_LAST
            END-OF-FIELDS
            ...
            START-OF-DATA
            CTA Comdty|0|1|EX|20210701|0.859|
            CTA Comdty|0|1|EX|20210702|0.8697|
            CTA Comdty|0|1|EX|20210706|0.874|
            CTA Comdty|0|1|EX|20210707|0.8763|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        actual_data_array = parser.get_history(Mock(), {"PX_LAST": "Price"},
                                               {"CTA Comdty": BloombergTicker("CTA Comdty")})

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (4, 1, 1))
        self.assertTrue(len(actual_data_array))  # not empty df

        expected_tickers_str_list = [BloombergTicker('CTA Comdty')]
        self.assertCountEqual(actual_data_array.tickers.values, expected_tickers_str_list)

        expected_fields_str_list = ['PX_LAST']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = ['2021-07-01', '2021-07-02', '2021-07-06', '2021-07-07']
        actual_datetime_strings = [datetime_as_string(datetime64(dt), unit='D') for dt in
                                   actual_data_array.dates.values]
        self.assertCountEqual(actual_datetime_strings, expected_datetime_strings)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_history_single_ticker_single_field_empty_response(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            PX_LAST
            END-OF-FIELDS
            ...
            START-OF-DATA
            RTYM1 Index|0|1|EX| | |
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        actual_data_array = parser.get_history(Mock(), {"PX_LAST": "Price"},
                                               {"RTYM1 Index": BloombergTicker("RTYM1 Index")})

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (0, 1, 1))
        self.assertFalse(len(actual_data_array))  # empty df

        expected_tickers_str_list = [BloombergTicker('RTYM1 Index')]
        self.assertCountEqual(actual_data_array.tickers.values, expected_tickers_str_list)

        expected_fields_str_list = ['PX_LAST']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_history_multiple_invalid_tickers_single_field(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            PX_LAST
            END-OF-FIELDS
            START-OF-DATA
            ASDVCXZASD Index|10|1| | | |
            ASDBVCX ComSADFdty|10|1| | | |
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        actual_data_array = parser.get_history(Mock(), {"PX_LAST": "Price"},
                                               {'ASDVCXZASD Index': BloombergTicker('ASDVCXZASD Index'),
                                                'ASDBVCX ComSADFdty': BloombergTicker('ASDBVCX ComSADFdty')})

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (0, 2, 1))
        self.assertFalse(len(actual_data_array))  # empty df

        expected_tickers_str_list = ['ASDVCXZASD Index', 'ASDBVCX ComSADFdty']
        self.assertCountEqual(actual_data_array.tickers.values, BloombergTicker.from_string(expected_tickers_str_list))

        expected_fields_str_list = ['PX_LAST']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_current_values_single_ticker_na_field(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            RTG_SP_LT_FC_ISSUER_CREDIT
            END-OF-FIELDS
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|RTG_SP_LT_FC_ISSUER_CREDIT|
            STT US Equity|0|1|N.A.|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {"RTG_SP_LT_FC_ISSUER_CREDIT": "Character"})

        self.assertEqual(df.shape, (1, 1))

        expected_active_tickers_str_list = ['STT US Equity']
        self.assertCountEqual(df.index.tolist(), expected_active_tickers_str_list)
        self.assertEqual(df.loc['STT US Equity', 'RTG_SP_LT_FC_ISSUER_CREDIT'], None)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_current_values_single_ticker_na_real_field(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            VOLATILITY_90D
            END-OF-FIELDS
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|VOLATILITY_90D|
            SOME SW Equity|0|1|N.A.|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {"VOLATILITY_90D": "Real"})

        self.assertEqual(df.shape, (1, 1))

        expected_active_tickers_str_list = ['SOME SW Equity']
        self.assertCountEqual(df.index.tolist(), expected_active_tickers_str_list)
        self.assertTrue(isna(df.loc['SOME SW Equity', 'VOLATILITY_90D']))

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_history_multiple_tickers_multiple_fields_multiple_dates(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            PX_OPEN
            PX_HIGH
            PX_LOW
            PX_LAST
            END-OF-FIELDS
            ...
            START-OF-DATA
            RTYM1 Index|0|5|EX| | | | | |
            CTA Comdty|0|5|EX|20210701|0.8505|0.8685|0.8492|0.859|
            CTA Comdty|0|5|EX|20210702|0.86|0.8715|0.8587|0.8697|
            CTA Comdty|0|5|EX|20210706|0.876|0.8889|0.8608|0.874|
            CTA Comdty|0|5|EX|20210707|0.874|0.8795|0.8657|0.8763|
            CTA Comdty|0|5|EX|20210708|0.8757|0.8763|0.863|0.8688|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        actual_data_array = parser.get_history(Mock(), {'PX_OPEN': "Price", 'PX_HIGH': "Price", 'PX_LOW': "Price",
                                                        'PX_LAST': "Price"},
                                               {'RTYM1 Index': BloombergTicker("RTYM1 Index"),
                                                'CTA Comdty': BloombergTicker('CTA Comdty')})

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (5, 2, 4))
        self.assertTrue(len(actual_data_array))
        self.assertEqual(actual_data_array.dtype, float64)

        expected_tickers_str_list = ['RTYM1 Index', 'CTA Comdty']
        self.assertCountEqual(actual_data_array.tickers.values, BloombergTicker.from_string(expected_tickers_str_list))

        expected_fields_str_list = ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = ['2021-07-01', '2021-07-02', '2021-07-06', '2021-07-07', '2021-07-08']
        actual_datetime_strings = [datetime_as_string(datetime64(dt), unit='D') for dt in
                                   actual_data_array.dates.values]
        self.assertCountEqual(actual_datetime_strings, expected_datetime_strings)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_history_single_ticker_multiple_fields_multiple_dates(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            PX_OPEN
            PX_HIGH
            PX_LOW
            PX_LAST
            PX_VOLUME
            END-OF-FIELDS
            ...
            START-OF-DATA
            CTA Comdty|0|5|EX|20210701|0.8505|0.8685|0.8492|0.859|19881|
            CTA Comdty|0|5|EX|20210702|0.86|0.8715|0.8587|0.8697|15106|
            CTA Comdty|0|5|EX|20210706|0.876|0.8889|0.8608|0.874|24926|
            CTA Comdty|0|5|EX|20210707|0.874|0.8795|0.8657|0.8763|12451|
            CTA Comdty|0|5|EX|20210708|0.8757|0.8763|0.863|0.8688|13261|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        actual_data_array = parser.get_history(Mock(), {'PX_OPEN': "Price", 'PX_HIGH': "Price", 'PX_LOW': "Price",
                                                        'PX_LAST': "Price", "PX_VOLUME": "Integer"},
                                               {"CTA Comdty": BloombergTicker("CTA Comdty")})

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (5, 1, 5))
        self.assertTrue(len(actual_data_array))
        self.assertEqual(actual_data_array.dtype, float64)

        expected_tickers_str_list = [BloombergTicker('CTA Comdty')]
        self.assertCountEqual(actual_data_array.tickers.values, expected_tickers_str_list)

        expected_fields_str_list = ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST', 'PX_VOLUME']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = ['2021-07-01', '2021-07-02', '2021-07-06', '2021-07-07', '2021-07-08']
        actual_datetime_strings = [datetime_as_string(datetime64(dt), unit='D') for dt in
                                   actual_data_array.dates.values]
        self.assertCountEqual(actual_datetime_strings, expected_datetime_strings)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_chain_single_ticker_single_field_multiple_tickers(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_CHAIN
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|FUT_CHAIN|
            RTYA Index|0|1|;2;5;1;4;RTYU17 Index;4;RTYZ17 Index;4;RTYH18 Index;4;RTYM18 Index;4;RTYU18 Index;|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {'FUT_CHAIN': "Bulk Format"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (1, 1))

        expected_active_tickers_str_list = ['RTYA Index']
        self.assertCountEqual(df.index.tolist(), expected_active_tickers_str_list)

        expected_tickers_str_list = ['RTYU17 Index', 'RTYZ17 Index', 'RTYH18 Index', 'RTYM18 Index', 'RTYU18 Index']
        self.assertCountEqual(df.loc['RTYA Index', 'FUT_CHAIN'], expected_tickers_str_list)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_chain_multiple_tickers_single_field_multiple_tickers(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_CHAIN
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|FUT_CHAIN|
            CTA Index|0|1|;2;2;1;4;CTU17 Index;4;CTZ17 Index;|
            RTYA Index|0|1|;2;5;1;4;RTYU17 Index;4;RTYZ17 Index;4;RTYH18 Index;4;RTYM18 Index;4;RTYU18 Index;|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {'FUT_CHAIN': "Bulk Format"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (2, 1))

        expected_active_tickers_str_list = ['CTA Index', 'RTYA Index']
        self.assertCountEqual(df.index.tolist(), expected_active_tickers_str_list)

        expected_tickers_str_list = ['RTYU17 Index', 'RTYZ17 Index', 'RTYH18 Index', 'RTYM18 Index', 'RTYU18 Index']
        self.assertCountEqual(df.loc['RTYA Index', 'FUT_CHAIN'], expected_tickers_str_list)

        expected_tickers_str_list = ['CTU17 Index', 'CTZ17 Index']
        self.assertCountEqual(df.loc['CTA Index', 'FUT_CHAIN'], expected_tickers_str_list)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_chain_multiple_tickers_single_field__correct_and_incorrect_ticker(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_CHAIN
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|FUT_CHAIN|
            RTYA Index|0|1|;2;5;1;4;RTYU17 Index;4;RTYZ17 Index;4;RTYH18 Index;4;RTYM18 Index;4;RTYU18 Index;|
            RTASYA Index|10|1| |
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {'FUT_CHAIN': "Bulk Format"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (2, 1))

        expected_active_tickers_str_list = ['RTASYA Index', 'RTYA Index']
        self.assertCountEqual(df.index.tolist(), expected_active_tickers_str_list)

        expected_tickers_str_list = ['RTYU17 Index', 'RTYZ17 Index', 'RTYH18 Index', 'RTYM18 Index', 'RTYU18 Index']
        self.assertCountEqual(df.loc['RTYA Index', 'FUT_CHAIN'], expected_tickers_str_list)
        self.assertCountEqual(df.loc['RTASYA Index', 'FUT_CHAIN'], [])

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_chain_single_ticker_single_field__incorrect_ticker(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_CHAIN
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|FUT_CHAIN|
            RTASYA Index|10|1| |
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {'FUT_CHAIN': "Bulk Format"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (1, 1))

        expected_active_tickers_str_list = ['RTASYA Index']
        self.assertCountEqual(df.index.tolist(), expected_active_tickers_str_list)
        self.assertCountEqual(df.loc['RTASYA Index', 'FUT_CHAIN'], [])

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_dates_multiple_tickers_single_field(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_NOTICE_FIRST
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|FUT_NOTICE_FIRST|
            RTYU17 Index|0|2|20170915|
            RTYZ17 Index|0|2|20171215|
            RTYH18 Index|0|2|20180316|
            RTYM18 Index|0|2|20180615|
            RTYU18 Index|0|2|20180921|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {"FUT_NOTICE_FIRST": "Date"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (5, 1))
        self.assertTrue(len(df))

        expected_tickers_str_list = ['RTYU17 Index', 'RTYZ17 Index', 'RTYH18 Index', 'RTYM18 Index', 'RTYU18 Index']
        self.assertCountEqual(df.index.tolist(), expected_tickers_str_list)

        expected_field = ['FUT_NOTICE_FIRST']
        self.assertEqual(df.columns, expected_field)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = ['2017-09-15', '2017-12-15', '2018-03-16', '2018-06-15', '2018-09-21']
        actual_datetime_strings = [datetime_as_string(datetime64(*dt), unit='D') for dt in df.values]
        self.assertCountEqual(actual_datetime_strings, expected_datetime_strings)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_dates_multiple_tickers_multiple_fields(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_NOTICE_FIRST
            LAST_TRADEABLE_DT
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|FUT_NOTICE_FIRST|LAST_TRADEABLE_DT|
            CTH4 Comdty|0|2|20240223|20240306|
            CTK4 Comdty|0|2|N.S.|N.S.|
            RTYU1 Index|0|2|20210917|20210917|
            RTYZ1 Index|0|2|20211217|20211217|
            RTYU2 Index|0|2|20220916|20220916|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {'FUT_NOTICE_FIRST': "Date", 'LAST_TRADEABLE_DT': "Date"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (5, 2))
        self.assertTrue(len(df))

        expected_tickers_str_list = ['CTH4 Comdty', 'CTK4 Comdty', 'RTYU1 Index', 'RTYZ1 Index', 'RTYU2 Index']
        self.assertCountEqual(df.index.tolist(), expected_tickers_str_list)

        expected_fields_list = ['FUT_NOTICE_FIRST', 'LAST_TRADEABLE_DT']
        self.assertCountEqual(df.columns, expected_fields_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = [['2024-02-23', '2024-03-06'], ["NaT", "NaT"], ['2021-09-17', '2021-09-17'],
                                     ['2021-12-17', '2021-12-17'], ['2022-09-16',
                                                                    '2022-09-16']]  # For datetime64[ns] types, NaT represents missing values.
        actual_datetime_strings = [
            [datetime_as_string(datetime64(dt[0]), unit='D'), datetime_as_string(datetime64(dt[1]), unit='D')] for dt in
            df.values]
        self.assertCountEqual(actual_datetime_strings, expected_datetime_strings)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_current_values__single_ticker_single_field(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FIELDS
            NAME
            END-OF-FIELDS
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|NAME|
            SPY US Equity|0|1|SPDR S&P 500 ETF TRUST|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {"NAME": "String"})

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (1, 1))
        self.assertTrue(df.values == ["SPDR S&P 500 ETF TRUST"])

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_current_values__multiple_tickers_multiple_fields(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FIELDS
            NAME
            PX_LAST
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|NAME|PX_LAST|
            SPY US Equity|0|2|SPDR S&P 500 ETF TRUST|67.830000|
            MSFT US Equity|0|2|MICROSOFT CORP|39.670000|
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        expected_df = QFDataFrame.from_dict({
            'NAME': {'SPY US Equity': 'SPDR S&P 500 ETF TRUST', 'MSFT US Equity': 'MICROSOFT CORP'},
            'PX_LAST': {'SPY US Equity': 67.83, 'MSFT US Equity': 39.67}
        })
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {"NAME": "String", "PX_LAST": "Price"})
        assert_frame_equal(expected_df, df, check_names=False)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_current_values__multiple_tickers_multiple_fields__incorrect_ticker(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FIELDS
            NAME
            PX_LAST
            END-OF-FIELDS
            ...
            START-OF-DATA
            SECURITIES|ERROR CODE|NUM FLDS|NAME|PX_LAST|
            SPY US Equity|0|2|SPDR S&P 500 ETF TRUST|68.320000|
            Incorrect Equity|10|2| | |
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        expected_df = QFDataFrame.from_dict({
            'NAME': {'SPY US Equity': 'SPDR S&P 500 ETF TRUST', 'Incorrect Equity': None},
            'PX_LAST': {'SPY US Equity': 68.32, 'Incorrect Equity': nan}
        })
        expected_df['PX_LAST'] = expected_df['PX_LAST'].astype(float64)
        parser = BloombergBeapHapiParser()
        df = parser.get_current_values(Mock(), {"NAME": "String", "PX_LAST": "Price"})
        assert_frame_equal(expected_df, df, check_names=False)


if __name__ == '__main__':
    unittest.main()
