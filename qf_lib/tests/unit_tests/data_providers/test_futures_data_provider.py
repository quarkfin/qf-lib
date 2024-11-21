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
from typing import Optional
from unittest import TestCase
from unittest.mock import patch

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.futures_data_provider import FuturesDataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_dataframes_equal


@patch.multiple(Ticker, __abstractmethods__=set())
@patch.multiple(FutureTicker, __abstractmethods__=set())
class TestFuturesDataProvider(TestCase):

    @classmethod
    @patch.multiple(FuturesDataProvider, __abstractmethods__=set())
    def setUpClass(cls) -> None:
        cls.data_provider = FuturesDataProvider()

    @patch.multiple(Ticker, __abstractmethods__=set())
    @patch.multiple(FutureTicker, __abstractmethods__=set())
    def setUp(self) -> None:
        # Mock the abstractmethod expiration_date_field_str_map
        expiration_date_field_str_map_patcher = patch.object(FuturesDataProvider, 'expiration_date_field_str_map')
        mocked_expiration_date_field_str_map_patcher = expiration_date_field_str_map_patcher.start()
        mocked_expiration_date_field_str_map_patcher.side_effect = self._mock_expiration_date_field_str_map_patcher
        self.addCleanup(mocked_expiration_date_field_str_map_patcher.stop)

        # Mock the abstractmethod _get_futures_chain_dict
        _get_futures_chain_dict_patcher = patch.object(FuturesDataProvider, '_get_futures_chain_dict')
        mocked_get_futures_chain_dict_patcher = _get_futures_chain_dict_patcher.start()
        mocked_get_futures_chain_dict_patcher.side_effect = self._mock__get_futures_chain_dict
        self.addCleanup(mocked_get_futures_chain_dict_patcher.stop)

    def test_str_to_expiration_date_field_map(self):
        actual_mapping = self.data_provider.str_to_expiration_date_field_map()
        self.assertEqual(actual_mapping["LAST_TRADEABLE_DATE"], ExpirationDateField.LastTradeableDate)
        self.assertEqual(actual_mapping["FIRST_NOTICE"], ExpirationDateField.FirstNotice)

    def test_get_futures_chain_tickers__single_ticker__all_dates_available(self):
        futures_chain = self.data_provider.get_futures_chain_tickers(
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"), ExpirationDateField.all_dates()
        )

        expected_chain = {
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"): QFDataFrame(
                index=[Ticker("C H1 Comdty", None, None), Ticker("C N1 Comdty", None, None),
                       Ticker("C M1 Comdty", None, None)],
                data=[[datetime(2021, 3, 1), datetime(2021, 3, 10)], [datetime(2021, 5, 1), datetime(2021, 5, 10)],
                      [datetime(2021, 7, 1), datetime(2021, 7, 10)]],
                columns=ExpirationDateField.all_dates())
        }
        for key in futures_chain.keys():
            self.assertTrue(key in expected_chain.keys())
            assert_dataframes_equal(futures_chain[key], expected_chain[key])

    def test_get_futures_chain_tickers__multiple_tickers__all_dates_available(self):
        futures_chain = self.data_provider.get_futures_chain_tickers(
            [FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"),
             FutureTicker("Wheat", "W {} Comdty", 1, 5, 10)], ExpirationDateField.all_dates(),
        )

        expected_chain = {
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"): QFDataFrame(
                index=[Ticker("C H1 Comdty", None, None), Ticker("C N1 Comdty", None, None),
                       Ticker("C M1 Comdty", None, None)],
                data=[[datetime(2021, 3, 1), datetime(2021, 3, 10)], [datetime(2021, 5, 1), datetime(2021, 5, 10)],
                      [datetime(2021, 7, 1), datetime(2021, 7, 10)]],
                columns=ExpirationDateField.all_dates()),
            FutureTicker("Wheat", "W {} Comdty", 1, 5, 10): QFDataFrame(
                index=[Ticker("W H1 Comdty", None, None), Ticker("W N1 Comdty", None, None),
                       Ticker("W M1 Comdty", None, None)],
                data=[[datetime(2022, 3, 1), datetime(2022, 3, 10)], [datetime(2022, 5, 1), datetime(2022, 5, 10)],
                      [datetime(2022, 7, 1), datetime(2022, 7, 10)]],
                columns=ExpirationDateField.all_dates()),
        }
        for key in futures_chain.keys():
            self.assertTrue(key in expected_chain.keys())
            assert_dataframes_equal(futures_chain[key], expected_chain[key])

    def test_get_futures_chain_tickers__single_ticker__test_single_date(self):
        futures_chain = self.data_provider.get_futures_chain_tickers(
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"), ExpirationDateField.LastTradeableDate
        )

        expected_chain = {
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"): QFDataFrame(
                index=[Ticker("C H1 Comdty", None, None), Ticker("C N1 Comdty", None, None),
                       Ticker("C M1 Comdty", None, None)],
                data=[[datetime(2021, 3, 10)], [datetime(2021, 5, 10)], [datetime(2021, 7, 10)]],
                columns=[ExpirationDateField.LastTradeableDate]),
            FutureTicker("Wheat", "W {} Comdty", 1, 5, 5): QFDataFrame(
                index=[Ticker("W H1 Comdty", None, None), Ticker("W N1 Comdty", None, None),
                       Ticker("W M1 Comdty", None, None)],
                data=[[datetime(2022, 3, 10)], [datetime(2022, 5, 10)], [datetime(2022, 7, 10)]],
                columns=[ExpirationDateField.LastTradeableDate]),
        }
        for key in futures_chain.keys():
            self.assertTrue(key in expected_chain.keys())
            assert_dataframes_equal(futures_chain[key], expected_chain[key])

    def test_get_futures_chain_tickers__multiple_tickers__test_single_date(self):
        futures_chain = self.data_provider.get_futures_chain_tickers(
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"), ExpirationDateField.LastTradeableDate
        )

        expected_chain = {
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"): QFDataFrame(
                index=[Ticker("C H1 Comdty", None, None), Ticker("C N1 Comdty", None, None),
                       Ticker("C M1 Comdty", None, None)],
                data=[[datetime(2021, 3, 10)], [datetime(2021, 5, 10)], [datetime(2021, 7, 10)]],
                columns=[ExpirationDateField.LastTradeableDate])
        }
        for key in futures_chain.keys():
            self.assertTrue(key in expected_chain.keys())
            assert_dataframes_equal(futures_chain[key], expected_chain[key])

    @staticmethod
    def _mock_expiration_date_field_str_map_patcher(_: Optional = None):
        return {
            ExpirationDateField.FirstNotice: "FIRST_NOTICE",
            ExpirationDateField.LastTradeableDate: "LAST_TRADEABLE_DATE",
        }

    @staticmethod
    def _mock__get_futures_chain_dict(tickers, expiration_date_fields):
        data = {
            FutureTicker("Corn", "C {} Comdty", 1, 5, 10, "HMUZ"):
                QFDataFrame({
                    "FIRST_NOTICE": [datetime(2021, 3, 1), datetime(2021, 5, 1), datetime(2021, 7, 1)],
                    "LAST_TRADEABLE_DATE": [datetime(2021, 3, 10), datetime(2021, 5, 10), datetime(2021, 7, 10)]
                }, index=[Ticker("C H1 Comdty", None, None), Ticker("C N1 Comdty", None, None),
                          Ticker("C M1 Comdty", None, None)]),
            FutureTicker("Wheat", "W {} Comdty", 1, 5, 10):
                QFDataFrame({
                    "FIRST_NOTICE": [datetime(2022, 3, 1), datetime(2022, 5, 1), datetime(2022, 7, 1)],
                    "LAST_TRADEABLE_DATE": [datetime(2022, 3, 10), datetime(2022, 5, 10), datetime(2022, 7, 10)]
                }, index=[Ticker("W H1 Comdty", None, None), Ticker("W N1 Comdty", None, None),
                          Ticker("W M1 Comdty", None, None)]),
        }

        tickers, _ = convert_to_list(tickers, FutureTicker)
        results = {}
        for ticker in tickers:
            container = data[ticker]
            if isinstance(container, QFDataFrame):
                container = container.loc[:, expiration_date_fields]
            results[ticker] = container

        return results
