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
from unittest.mock import patch

from pandas import date_range

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.signals.backtest_signals_register import BacktestSignalsRegister
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker


class TestSignalsRegister(unittest.TestCase):
    def test_get_signals__single_contract(self):
        """
        Save signals, which belong to one ticker (contract). The returned signals data frame should contain only one
        column, named after the ticker and used model.
        """
        ticker = BloombergTicker("Example Index")
        number_of_days = 30
        start_date = str_to_date("2000-01-01")
        end_date = start_date + RelativeDelta(days=number_of_days-1)

        signals_register = BacktestSignalsRegister()

        for date in date_range(start_date, end_date, freq="D"):
            signals_register.save_signals([Signal(ticker, Exposure.LONG, 0.0, 17, date)])

        signals_df = signals_register.get_signals()

        self.assertEqual(type(signals_df), QFDataFrame)
        self.assertEqual(signals_df.shape, (number_of_days, 1))

    def test_get_signals__multiple_tickers(self):
        """
        Save signals, which belong to multiple tickers.
        """
        tickers = [BloombergTicker("Example Index"), BloombergTicker("Example 2 Index")]

        number_of_days = 30
        start_date = str_to_date("2000-01-01")
        end_date = start_date + RelativeDelta(days=number_of_days - 1)

        signals_register = BacktestSignalsRegister()

        for date in date_range(start_date, end_date, freq="D"):
            signals_register.save_signals([Signal(ticker, Exposure.LONG, 0.0, 17, date) for ticker in tickers])

        signals_df = signals_register.get_signals()

        self.assertEqual(type(signals_df), QFDataFrame)
        self.assertEqual(signals_df.shape, (number_of_days, 2))

    def test_get_signals__one_ticker_multiple_signals(self):
        """
        Save signals belonging to one ticker. In this case, even if multiple different signals will be generated for
        one date, only one of them will be returned (always the first one).
        """
        ticker = BloombergTicker("Example Index")
        number_of_days = 30
        start_date = str_to_date("2000-01-01")
        end_date = start_date + RelativeDelta(days=number_of_days - 1)

        signals_register = BacktestSignalsRegister()

        for date in date_range(start_date, end_date, freq="D"):
            signals_register.save_signals([Signal(ticker, Exposure.LONG, 0.0, 17, date)])
            signals_register.save_signals([Signal(ticker, Exposure.SHORT, 0.0, 17, date)])

        signals_df = signals_register.get_signals()

        self.assertEqual(type(signals_df), QFDataFrame)
        self.assertEqual(signals_df.shape, (number_of_days, 1))

        for column, tms in signals_df.iteritems():
            self.assertTrue(all(s.suggested_exposure == Exposure.LONG for s in tms))

    @patch.object(BloombergFutureTicker, "ticker")
    def test_get_signals__one_future_ticker(self, ticker_mock):
        fut_ticker_1 = BloombergFutureTicker("Ticker name", "family id", 1, 1)
        ticker_mock.return_value = "Specific ticker"

        number_of_days = 30
        start_date = str_to_date("2000-01-01")
        rolling_date = start_date + RelativeDelta(days=number_of_days - 1)

        signals_register = BacktestSignalsRegister()

        for date in date_range(start_date, rolling_date, freq="D"):
            signals_register.save_signals([Signal(fut_ticker_1, Exposure.LONG, 0.0, 17, date)])

        signals_df = signals_register.get_signals()

        self.assertEqual(type(signals_df), QFDataFrame)
        self.assertEqual(signals_df.shape, (number_of_days, 1))
