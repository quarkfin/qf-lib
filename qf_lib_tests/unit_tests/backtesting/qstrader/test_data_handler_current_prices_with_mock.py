import unittest
from datetime import datetime
from unittest import TestCase

from mockito import mock, when, ANY
from pandas import Series, Panel, date_range

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.testing_tools.containers_comparison import assert_series_equal


class TestCurrentPricesFromDataHandler(TestCase):
    def setUp(self):
        self.timer = SettableTimer()

        self.tickers = [QuandlTicker("MSFT", "WIKI"), QuandlTicker("AAPL", "WIKI")]
        self.price_data_provider_mock = _create_price_provider_mock(
            self.tickers, price_fields=[PriceField.Open, PriceField.Close]
        )

        self.data_handler = DataHandler(self.price_data_provider_mock, self.timer)

    def test_before_data_starts(self):
        self._assert_current_prices_are_correct("2009-12-28 06:00:00.000000", None)

    def test_at_open_when_data_available_for_every_ticker(self):
        self._assert_current_prices_are_correct("2009-12-28 09:30:00.000000", [25.0, 27.0])

    def test_in_the_middle_of_a_trading_session_when_data_available_for_every_ticker(self):
        self._assert_current_prices_are_correct("2009-12-28 12:00:00.000000", None)

    def test_at_the_market_close_when_data_available_for_every_ticker(self):
        self._assert_current_prices_are_correct("2009-12-28 16:00:00.000000", [26.0, 28.0])

    def test_at_market_open_when_data_available_for_the_second_ticker(self):
        self._assert_current_prices_are_correct("2009-12-29 09:30:00.000000", [None, 29.0])

    def test_in_the_middle_of_a_trading_session_when_data_available_for_the_second_ticker(self):
        self._assert_current_prices_are_correct("2009-12-29 12:00:00.000000", None)

    def test_at_market_close_when_data_available_for_the_second_ticker(self):
        self._assert_current_prices_are_correct("2009-12-29 16:00:00.000000", [None, 30.0])

    def test_at_market_open_when_data_available_for_the_first_ticker(self):
        self._assert_current_prices_are_correct("2009-12-30 09:30:00.000000", [31.0, None])

    def test_at_market_close_when_data_available_for_the_first_ticker(self):
        self._assert_current_prices_are_correct("2009-12-30 16:00:00.000000", [32.0, None])

    def test_after_market_close_when_data_is_not_available_for_anything_anymore(self):
        self._assert_current_prices_are_correct("2009-12-30 20:00:00.000000", None)

    def _assert_current_prices_are_correct(self, curr_time_str, expected_values):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        expected_series = Series(data=expected_values, index=self.tickers)
        actual_series = self.data_handler.get_current_price(self.tickers)
        assert_series_equal(expected_series, actual_series, check_names=False)


class TestLastAvailablePricesFromDataHandler(TestCase):
    def setUp(self):
        self.timer = SettableTimer()

        self.tickers = [QuandlTicker("MSFT", "WIKI"), QuandlTicker("AAPL", "WIKI")]
        self.price_data_provider_mock = _create_price_provider_mock(
            self.tickers, price_fields=[PriceField.Open, PriceField.Close]
        )

        self.data_handler = DataHandler(self.price_data_provider_mock, self.timer)

    def test_before_data_starts(self):
        self._assert_last_prices_are_correct("2009-12-28 06:00:00.000000", None)

    def test_at_open_when_data_available_for_every_ticker(self):
        self._assert_last_prices_are_correct("2009-12-28 09:30:00.000000", [25.0, 27.0])

    def test_in_the_middle_of_a_trading_session_when_data_available_fo(self):
        self._assert_last_prices_are_correct("2009-12-30 09:30:00.000000", [31.0, 30.0])

    def test_at_market_close_when_data_available_for_the_first_ticker(self):
        self._assert_last_prices_are_correct("2009-12-30 16:00:00.000000", [32.0, 30.0])

    def test_after_market_close_when_data_is_not_available_for_anything_anymore(self):
        self._assert_last_prices_are_correct("2009-12-30 20:00:00.000000", [32.0, 30.0])

    def _assert_last_prices_are_correct(self, curr_time_str, expected_values):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        expected_series = Series(data=expected_values, index=self.tickers)
        actual_series = self.data_handler.get_last_available_price(self.tickers)
        assert_series_equal(expected_series, actual_series, check_names=False)


def _create_price_provider_mock(tickers, price_fields):
    mock_data_panel = Panel(
        items=date_range(start='2009-12-28', end='2009-12-30', freq='D'),
        major_axis=tickers,
        minor_axis=price_fields,
        data=[
            # 2009-12-28
            [
                # Open Close
                [25.0, 26.0],  # MSFT
                [27.0, 28.0]   # AAPL
            ],
            # 2009-12-29
            [
                # Open Close
                [None, None],  # MSFT
                [29.0, 30.0]   # AAPL
            ],
            # 2009-12-30
            [
                # Open Close
                [31.0, 32.0],  # MSFT
                [None, None]   # AAPL
            ]
        ]
    )

    price_data_provider_mock = mock(strict=True)  # type: GeneralPriceProvider
    when(price_data_provider_mock).get_price(
        tickers, price_fields, ANY(datetime), ANY(datetime)
    ).thenReturn(mock_data_panel)

    return price_data_provider_mock


if __name__ == '__main__':
    unittest.main()
