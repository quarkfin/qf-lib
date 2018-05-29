import unittest
from unittest import TestCase

import pandas as pd
from os.path import join

from qf_lib.backtesting.qstrader.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings
from qf_lib.testing_tools.containers_comparison import assert_series_equal

settings = Settings(join(get_src_root(), 'qf_lib_tests', 'unit_tests', 'config', 'test_settings.json'))
bbg_provider = BloombergDataProvider(settings)
bbg_provider.connect()


@unittest.skipIf(not bbg_provider.connected, "No Bloomberg connection")
class TestDataHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spx_index_ticker = BloombergTicker("SPX Index")
        cls.google_ticker = BloombergTicker("GOOGL US Equity")
        cls.microsoft_ticker = BloombergTicker("MSFT US Equity")

        cls.start_date = str_to_date("2018-01-02")
        cls.end_date = str_to_date("2018-01-31")
        cls.end_date_trimmed = str_to_date("2018-01-30")

    def setUp(self):
        self.price_data_provider = bbg_provider
        self.assets_prices_df = PricesSeries(
            index=pd.date_range(self.start_date, self.end_date),
            name=self.spx_index_ticker
        )

        self.timer = SettableTimer()
        self.data_handler = DataHandler(self.price_data_provider, self.timer)

    def test_get_price_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2018-02-12 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date)

    def test_get_price_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 21:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date)

    def test_get_price_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close,
                                                 self.start_date, self.end_date)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date_trimmed)

    def test_get_price_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(str_to_date("2018-01-30 18:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_price(self.spx_index_ticker, PriceField.Close, self.start_date,
                                                 self.end_date_trimmed)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date_trimmed)

    def test_get_last_price_single_ticker(self):
        # just test if getting single ticker value works, when a single ticker (not wrapped in a list) is passed
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        single_price = self.data_handler.get_last_available_price(self.spx_index_ticker)
        self.assertTrue(isinstance(single_price, float))

        # during the trading session
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        during_the_day_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

        self.assertEqual(during_the_day_last_prices.index[0], self.spx_index_ticker)
        self.assertEqual(during_the_day_last_prices[0], single_price)

        # after the trading session
        self.timer.set_current_time(str_to_date("2018-01-31 20:00:00.000000", DateFormat.FULL_ISO))
        after_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

        self.assertEqual(after_close_last_prices.index[0], self.spx_index_ticker)
        self.assertNotEqual(after_close_last_prices[0], during_the_day_last_prices[0])

        # before the trading session
        self.timer.set_current_time(str_to_date("2018-01-31 07:00:00.000000", DateFormat.FULL_ISO))
        before_close_last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker])

        self.assertEqual(before_close_last_prices.index[0], self.spx_index_ticker)
        self.assertNotEqual(before_close_last_prices[0], during_the_day_last_prices[0])
        self.assertNotEqual(before_close_last_prices[0], after_close_last_prices[0])

    def test_get_last_price_with_multiple_tickers_when_current_data_is_unavailable(self):
        self.timer.set_current_time(str_to_date("2018-01-01 12:00:00.000000", DateFormat.FULL_ISO))
        last_prices = self.data_handler.get_last_available_price([self.spx_index_ticker, self.google_ticker])

        self.assertEqual(last_prices.index[0], self.spx_index_ticker)
        self.assertEqual(last_prices.index[1], self.google_ticker)

    def test_get_last_price_with_empty_tickers_list(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        last_prices = self.data_handler.get_last_available_price([])
        assert_series_equal(last_prices, pd.Series())

    def test_get_history_when_end_date_is_in_the_past(self):
        self.timer.set_current_time(str_to_date("2018-02-12 00:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date)

    def test_get_history_when_end_date_is_today_after_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 21:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date)

    def test_get_history_when_end_date_is_today_before_market_close(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date_trimmed)

    def test_get_history_when_end_date_is_tomorrow(self):
        self.timer.set_current_time(str_to_date("2018-01-30 18:00:00.000000", DateFormat.FULL_ISO))
        prices_tms = self.data_handler.get_history(self.spx_index_ticker, 'PX_TO_BOOK_RATIO',
                                                   self.start_date, self.end_date_trimmed)

        self.assertEqual(prices_tms.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(prices_tms.index[-1].to_pydatetime(), self.end_date_trimmed)

    def test_get_history_with_multiple_tickers(self):
        self.timer.set_current_time(str_to_date("2018-01-31 12:00:00.000000", DateFormat.FULL_ISO))
        resilt_df = self.data_handler.get_history([self.microsoft_ticker, self.google_ticker], 'PX_TO_BOOK_RATIO',
                                                  self.start_date, self.end_date_trimmed)

        self.assertEqual(resilt_df.columns[0], self.microsoft_ticker)
        self.assertEqual(resilt_df.columns[1], self.google_ticker)
        self.assertEqual(resilt_df.index[0].to_pydatetime(), self.start_date)
        self.assertEqual(resilt_df.index[-1].to_pydatetime(), self.end_date_trimmed)
        self.assertEqual(resilt_df.shape, (20, 2))


if __name__ == '__main__':
    unittest.main()
