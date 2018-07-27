import unittest
from datetime import datetime

import pandas as pd
from mockito import mock, when

import qf_lib.testing_tools.containers_comparison as tt
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider
from qf_lib.data_providers.price_data_provider import DataProvider


class TestPrefetchingDataProvider(unittest.TestCase):
    def setUp(self):
        self.start_date = datetime(2018, 2, 4)
        self.end_date = datetime(2018, 2, 10)

        self.msft_ticker = BloombergTicker("MSFT US Equity")
        self.google_ticker = BloombergTicker("GOOGL US Equity")
        self.apple_ticker = BloombergTicker("AAPL US Equity")

        self.cached_dates = pd.date_range(self.start_date, self.end_date)
        self.cached_tickers = [self.msft_ticker, self.google_ticker]
        self.cached_fields = [PriceField.Open, PriceField.Close, PriceField.Volume]

        self.data_provider = self.mock_data_provider()
        self.prefetching_data_provider = PrefetchingDataProvider(
            self.data_provider, self.cached_tickers, self.cached_fields, self.start_date, self.end_date
        )

    def mock_data_provider(self) -> DataProvider:
        data_provider = mock(strict=True)  # type: DataProvider

        when(data_provider).get_price(
            self.cached_tickers, self.cached_fields, self.start_date, self.end_date
        ).thenReturn(
            pd.Panel(
                items=self.cached_dates,
                major_axis=self.cached_tickers,
                minor_axis=self.cached_fields
            )
        )

        return data_provider

    def test_get_price_with_single_ticker(self):
        actual_frame = self.prefetching_data_provider.get_price(
            self.msft_ticker, self.cached_fields, self.start_date, self.end_date)

        expected_frame = QFDataFrame(index=self.cached_dates, columns=self.cached_fields)

        tt.assert_dataframes_equal(expected_frame, actual_frame, check_index_type=True, check_column_type=True)

    def test_get_price_with_single_field(self):
        actual_frame = self.prefetching_data_provider.get_price(
            self.cached_tickers, PriceField.Volume, self.start_date, self.end_date)
        expected_frame = QFDataFrame(index=self.cached_dates, columns=self.cached_tickers)

        tt.assert_dataframes_equal(expected_frame, actual_frame, check_index_type=True, check_column_type=True)

    def test_get_price_with_the_same_start_and_end_dates(self):
        actual_frame = self.prefetching_data_provider.get_price(
            self.cached_tickers, self.cached_fields, self.start_date, self.start_date)

        expected_frame = QFDataFrame(index=self.cached_tickers, columns=self.cached_fields)

        tt.assert_dataframes_equal(expected_frame, actual_frame, check_index_type=True, check_column_type=True)

    def test_get_price_with_multiple_tickers_and_fields(self):
        actual_panel = self.prefetching_data_provider.get_price(
            self.cached_tickers, self.cached_fields, self.start_date, self.end_date)

        expected_panel = pd.Panel(
            items=self.cached_dates, major_axis=self.cached_tickers, minor_axis=self.cached_fields)

        tt.assert_same_axis_values(expected_panel.items, actual_panel.items)
        tt.assert_same_axis_values(expected_panel.major_axis, actual_panel.major_axis)
        tt.assert_same_axis_values(expected_panel.minor_axis, actual_panel.minor_axis)

    def test_get_price_with_uncached_tickers(self):
        with self.assertRaises(ValueError):
            _ = self.prefetching_data_provider.get_price(
                [self.msft_ticker, self.google_ticker, self.apple_ticker],
                self.cached_fields,
                self.start_date, self.end_date
            )

    def test_get_price_with_uncached_fields(self):
        with self.assertRaises(ValueError):
            _ = self.prefetching_data_provider.get_price(
                self.cached_tickers,
                PriceField.ohlcv(),
                self.start_date, self.end_date
            )

    def test_get_price_with_uncached_dates(self):
        with self.assertRaises(ValueError):
            _ = self.prefetching_data_provider.get_price(
                self.cached_tickers,
                self.cached_fields,
                self.start_date - RelativeDelta(days=1), self.end_date + RelativeDelta(days=2)
            )


if __name__ == '__main__':
    unittest.main()
