import unittest
from datetime import datetime
from unittest import TestCase

import pandas as pd
from mockito import mock, when, ANY
from pandas import Series, date_range

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.testing_tools.containers_comparison import assert_series_equal, assert_dataframes_equal


class Test_DataHandler_CurrentPrices(TestCase):
    def setUp(self):
        self.timer, self.tickers, _, self.data_handler = _get_test_case_set_up()

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


class Test_DataHandler_LastAvailablePrices(TestCase):
    def setUp(self):
        self.timer, self.tickers, _, self.data_handler = _get_test_case_set_up()

    def test_before_data_starts(self):
        self._assert_last_prices_are_correct("2009-12-28 06:00:00.000000", None)

    def test_at_open_when_data_available_for_every_ticker(self):
        self._assert_last_prices_are_correct("2009-12-28 09:30:00.000000", [25.0, 27.0])

    def test_at_market_open_when_data_available_for_the_first_ticker(self):
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


class Test_DataHandler_LastAvailableBar(TestCase):
    def setUp(self):
        self.timer, self.tickers, self.price_fields, self.data_handler = _get_test_case_set_up()
        self.tickers_index = pd.Index(self.tickers, name='tickers')
        self.fields_index = pd.Index(self.price_fields, name='fields')

    def test_after_market_close_when_bar_is_available_for_every_ticker(self):
        self._assert_last_bars_are_correct("2009-12-28 16:00:00.000000", [
            [25.0, 25.1, 25.2, 26.0, 25.3],  # MSFT 2009-12-28
            [27.0, 27.1, 27.2, 28.0, 27.3]   # APPL 2009-12-28
        ])

    def test_on_open_when_only_data_from_yesterday_available(self):
        self._assert_last_bars_are_correct("2009-12-29 09:30:00.000000", [
            [25.0, 25.1, 25.2, 26.0, 25.3],  # MSFT 2009-12-28
            [27.0, 27.1, 27.2, 28.0, 27.3]   # APPL 2009-12-28
        ])

    def test_in_the_middle_of_a_trading_session(self):
        self._assert_last_bars_are_correct("2009-12-29 12:30:00.000000", [
            [25.0, 25.1, 25.2, 26.0, 25.3],  # MSFT 2009-12-28
            [27.0, 27.1, 27.2, 28.0, 27.3]   # APPL 2009-12-28
        ])

    def test_at_market_close_when_data_available_for_the_second_ticker_only(self):
        self._assert_last_bars_are_correct("2009-12-29 16:00:00.000000", [
            [25.0, 25.1, 25.2, 26.0, 25.3],  # MSFT 2009-12-28
            [29.0, 29.1, 29.2, 30.0, 29.3]   # APPL 2009-12-29
        ])

    def _assert_last_bars_are_correct(self, curr_time_str, expected_values):
        current_time = str_to_date(curr_time_str, DateFormat.FULL_ISO)
        self.timer.set_current_time(current_time)
        expected_dataframe = pd.DataFrame(data=expected_values, index=self.tickers_index, columns=self.fields_index)
        actual_dataframe = self.data_handler.get_last_available_bar(self.tickers)
        assert_dataframes_equal(expected_dataframe, actual_dataframe, check_names=False)


# UTILITY FUNCTIONS; used for setting up TestCases
def _get_test_case_set_up():
    timer = SettableTimer()

    tickers = [QuandlTicker("MSFT", "WIKI"), QuandlTicker("AAPL", "WIKI")]
    price_fields = PriceField.ohlcv()
    price_data_provider_mock = _create_price_provider_mock(
        tickers, price_fields=price_fields
    )

    data_handler = DataHandler(price_data_provider_mock, timer)

    return timer, tickers, price_fields, data_handler


def _create_price_provider_mock(tickers, price_fields):
    mock_data_array = QFDataArray.create(
        dates=date_range(start='2009-12-28', end='2009-12-30', freq='D'),
        tickers=tickers,
        fields=price_fields,
        data=[
            # 2009-12-28
            [
                # Open High  Low   Close Volume
                [25.0, 25.1, 25.2, 26.0, 25.3],  # MSFT
                [27.0, 27.1, 27.2, 28.0, 27.3]   # AAPL
            ],
            # 2009-12-29
            [
                # Open High  Low   Close Volume
                [None, None, None, None, None],  # MSFT
                [29.0, 29.1, 29.2, 30.0, 29.3]   # AAPL
            ],
            # 2009-12-30
            [
                # Open High  Low   Close Volume
                [31.0, 31.1, 31.2, 32.0, 31.3],  # MSFT
                [None, None, None, None, None]   # AAPL
            ]
        ]
    )

    price_data_provider_mock = mock(strict=True)  # type: GeneralPriceProvider
    when(price_data_provider_mock).get_price(
        tickers, [PriceField.Open, PriceField.Close], ANY(datetime), ANY(datetime)
    ).thenReturn(mock_data_array.loc[:, :, [PriceField.Open, PriceField.Close]])

    when(price_data_provider_mock).get_price(
        tickers, price_fields, ANY(datetime), ANY(datetime)
    ).thenReturn(mock_data_array)

    return price_data_provider_mock


if __name__ == '__main__':
    unittest.main()
