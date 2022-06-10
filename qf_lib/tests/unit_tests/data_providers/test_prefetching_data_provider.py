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
from datetime import datetime
from unittest.mock import Mock

import pandas as pd
import numpy as np

import qf_lib.tests.helpers.testing_tools.containers_comparison as tt
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dimension_names import DATES, TICKERS, FIELDS
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider
from qf_lib.data_providers.data_provider import DataProvider


class TestPrefetchingDataProvider(unittest.TestCase):
    def setUp(self):
        self.msft_ticker = BloombergTicker("MSFT US Equity")
        self.google_ticker = BloombergTicker("GOOGL US Equity")
        self.apple_ticker = BloombergTicker("AAPL US Equity")

        self.start_date = datetime(2018, 2, 4)
        self.end_date = datetime(2018, 2, 10)
        self.frequency = Frequency.DAILY
        self.cached_tickers = [self.msft_ticker, self.google_ticker]
        self.cached_fields = [PriceField.Open, PriceField.Close, PriceField.Volume]

        self.cached_dates_idx = pd.date_range(self.start_date, self.end_date, name=DATES)
        self.cached_tickers_idx = pd.Index([self.msft_ticker, self.google_ticker], name=TICKERS)
        self.cached_fields_idx = pd.Index([PriceField.Open, PriceField.Close, PriceField.Volume], name=FIELDS)

        self.data_provider = self.mock_data_provider()
        self.prefetching_data_provider = PrefetchingDataProvider(
            self.data_provider, self.cached_tickers, self.cached_fields, self.start_date, self.end_date, self.frequency
        )

    def mock_data_provider(self) -> DataProvider:
        data_provider = Mock(spec=DataProvider)
        data_provider.get_price.return_value = QFDataArray.create(
            data=np.full((len(self.cached_dates_idx), len(self.cached_tickers), len(self.cached_fields)), 0),
            dates=self.cached_dates_idx,
            tickers=self.cached_tickers,
            fields=self.cached_fields
        )
        data_provider.get_futures_chain_tickers.return_value = dict()
        return data_provider

    def test_get_price_with_single_ticker(self):
        actual_frame = self.prefetching_data_provider.get_price(self.msft_ticker, self.cached_fields, self.start_date,
                                                                self.end_date, self.frequency)

        expected_frame = PricesDataFrame(data=np.full((len(self.cached_dates_idx), len(self.cached_fields_idx)), 0),
                                         index=self.cached_dates_idx,
                                         columns=self.cached_fields_idx)

        tt.assert_dataframes_equal(expected_frame, actual_frame, check_index_type=True, check_column_type=True)

    def test_get_price_with_single_field(self):
        actual_frame = self.prefetching_data_provider.get_price(self.cached_tickers, PriceField.Volume, self.start_date,
                                                                self.end_date, self.frequency)

        expected_frame = PricesDataFrame(data=np.full((len(self.cached_dates_idx), len(self.cached_tickers_idx)), 0),
                                         index=self.cached_dates_idx,
                                         columns=self.cached_tickers_idx)
        tt.assert_dataframes_equal(expected_frame, actual_frame, check_index_type=True, check_column_type=True)

    def test_get_price_with_the_same_start_and_end_dates(self):
        actual_frame = self.prefetching_data_provider.get_price(self.cached_tickers, self.cached_fields,
                                                                self.start_date, self.start_date, self.frequency)

        expected_frame = PricesDataFrame(data=np.full((len(self.cached_tickers_idx), len(self.cached_fields_idx)), 0),
                                         index=self.cached_tickers_idx,
                                         columns=self.cached_fields_idx)

        tt.assert_dataframes_equal(expected_frame, actual_frame, check_index_type=True, check_column_type=True)

    def test_get_price_with_multiple_tickers_and_fields(self):
        actual_array = self.prefetching_data_provider.get_price(self.cached_tickers, self.cached_fields,
                                                                self.start_date, self.end_date, self.frequency)

        tt.assert_lists_equal(list(self.cached_dates_idx), list(actual_array.dates.to_index().values))
        tt.assert_lists_equal(self.cached_tickers, list(actual_array.tickers.values))
        tt.assert_lists_equal(self.cached_fields, list(actual_array.fields.values))

    def test_get_price_with_uncached_tickers(self):
        with self.assertRaises(ValueError):
            _ = self.prefetching_data_provider.get_price([self.msft_ticker, self.google_ticker, self.apple_ticker],
                                                         self.cached_fields, self.start_date, self.end_date,
                                                         self.frequency)

    def test_get_price_with_uncached_fields(self):
        with self.assertRaises(ValueError):
            _ = self.prefetching_data_provider.get_price(self.cached_tickers, PriceField.ohlcv(), self.start_date,
                                                         self.end_date, self.frequency)

    def test_get_price_with_uncached_dates(self):
        with self.assertRaises(ValueError):
            _ = self.prefetching_data_provider.get_price(self.cached_tickers, self.cached_fields,
                                                         self.start_date - RelativeDelta(days=1),
                                                         self.end_date + RelativeDelta(days=2), self.frequency)


if __name__ == '__main__':
    unittest.main()
