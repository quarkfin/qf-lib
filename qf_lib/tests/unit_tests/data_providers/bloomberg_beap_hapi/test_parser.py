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

from numpy import datetime64, datetime_as_string

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
        actual_data_array = parser.get_history(Mock())

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (4, 1, 1))
        self.assertTrue(len(actual_data_array))  # not empty df

        expected_tickers_str_list = ['CTA Comdty']
        self.assertCountEqual(actual_data_array.tickers.values, expected_tickers_str_list)

        expected_fields_str_list = ['PX_LAST']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = ['2021-07-01', '2021-07-02', '2021-07-06', '2021-07-07']
        actual_datetime_strings = [datetime_as_string(datetime64(dt), unit='D') for dt in actual_data_array.dates.values]
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
        actual_data_array = parser.get_history(Mock())

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (0, 1, 1))
        self.assertFalse(len(actual_data_array))  # empty df

        expected_tickers_str_list = ['RTYM1 Index']
        self.assertCountEqual(actual_data_array.tickers.values, expected_tickers_str_list)

        expected_fields_str_list = ['PX_LAST']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

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
            PX_VOLUME
            END-OF-FIELDS
            ...
            START-OF-DATA
            RTYM1 Index|0|5|EX| | | | | | |
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
        actual_data_array = parser.get_history(Mock())

        self.assertEqual(type(actual_data_array), QFDataArray)
        self.assertEqual(actual_data_array.shape, (5, 2, 5))
        self.assertTrue(len(actual_data_array))

        expected_tickers_str_list = ['RTYM1 Index', 'CTA Comdty']
        self.assertCountEqual(actual_data_array.tickers.values, expected_tickers_str_list)

        expected_fields_str_list = ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST', 'PX_VOLUME']
        self.assertCountEqual(actual_data_array.fields.values, expected_fields_str_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = ['2021-07-01', '2021-07-02', '2021-07-06', '2021-07-07', '2021-07-08']
        actual_datetime_strings = [datetime_as_string(datetime64(dt), unit='D') for dt in actual_data_array.dates.values]
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
            RTYA Index                                        |RTYU17 Index
            RTYA Index                                        |RTYZ17 Index
            RTYA Index                                        |RTYH18 Index
            RTYA Index                                        |RTYM18 Index
            RTYA Index                                        |RTYU18 Index
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        data_dict = parser.get_chain(Mock())

        self.assertEqual(type(data_dict), dict)
        self.assertEqual(len(data_dict.keys()), 1)

        expected_active_ticker_str = 'RTYA Index'
        self.assertEqual(*data_dict.keys(), expected_active_ticker_str)

        expected_tickers_str_list = ['RTYU17 Index', 'RTYZ17 Index', 'RTYH18 Index', 'RTYM18 Index', 'RTYU18 Index']
        self.assertCountEqual(*data_dict.values(), expected_tickers_str_list)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_chain_mutiple_tickers_single_field_multiple_tickers(self, mock):
        mock.open.return_value = BytesIO(str.encode(dedent(
            """
            START-OF-FILE
            ...
            START-OF-FIELDS
            FUT_CHAIN
            END-OF-FIELDS
            ...
            START-OF-DATA
            CTA Comdty                                        |CTV1 Comdty
            CTA Comdty                                        |CTZ1 Comdty
            CTA Comdty                                        |CTH2 Comdty
            CTA Comdty                                        |CTK2 Comdty
            RTYA Index                                        |RTYU1 Index
            RTYA Index                                        |RTYZ1 Index
            RTYA Index                                        |RTYH2 Index
            RTYA Index                                        |RTYM2 Index
            RTYA Index                                        |RTYU2 Index
            END-OF-DATA
            ...
            END-OF-FILE
            """
        )))
        parser = BloombergBeapHapiParser()
        data_dict = parser.get_chain(Mock())

        self.assertEqual(type(data_dict), dict)
        self.assertEqual(len(data_dict.keys()), 2)

        expected_active_tickers_str_list = ['CTA Comdty', 'RTYA Index']
        self.assertCountEqual(list(data_dict.keys()), expected_active_tickers_str_list)

        expected_tickers_str_list = [['CTV1 Comdty', 'CTZ1 Comdty', 'CTH2 Comdty', 'CTK2 Comdty'], ['RTYU1 Index', 'RTYZ1 Index', 'RTYH2 Index', 'RTYM2 Index', 'RTYU2 Index']]
        self.assertCountEqual(list(data_dict.values()), expected_tickers_str_list)

    @patch('qf_lib.data_providers.bloomberg_beap_hapi.bloomberg_beap_hapi_parser.gzip')
    def test_get_dates_mutiple_tickers_single_field(self, mock):
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
        df = parser.get_current_values_dates_fields_format(Mock())

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
    def test_get_dates_mutiple_tickers_multiple_fields(self, mock):
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
        df = parser.get_current_values_dates_fields_format(Mock())

        self.assertEqual(type(df), QFDataFrame)
        self.assertEqual(df.shape, (5, 2))
        self.assertTrue(len(df))

        expected_tickers_str_list = ['CTH4 Comdty', 'CTK4 Comdty', 'RTYU1 Index', 'RTYZ1 Index', 'RTYU2 Index']
        self.assertCountEqual(df.index.tolist(), expected_tickers_str_list)

        expected_fields_list = ['FUT_NOTICE_FIRST', 'LAST_TRADEABLE_DT']
        self.assertCountEqual(df.columns, expected_fields_list)

        # Compare string values of dates (to simplify the numpy.datetime64 comparison)
        expected_datetime_strings = [['2024-02-23', '2024-03-06'], ["NaT", "NaT"], ['2021-09-17', '2021-09-17'],
                                     ['2021-12-17', '2021-12-17'], ['2022-09-16', '2022-09-16']]  # For datetime64[ns] types, NaT represents missing values.
        actual_datetime_strings = [[datetime_as_string(datetime64(dt[0]), unit='D'), datetime_as_string(datetime64(dt[1]), unit='D')] for dt in df.values]
        self.assertCountEqual(actual_datetime_strings, expected_datetime_strings)


if __name__ == '__main__':
    unittest.main()
