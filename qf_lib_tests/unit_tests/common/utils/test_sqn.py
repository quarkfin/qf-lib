import unittest
from unittest import TestCase

import pandas as pd

from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.returns.sqn import sqn_for100trades, avg_nr_of_trades_per1y, trade_based_cagr, \
    trade_based_max_drawdown, sqn
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class TestSqnUtils(TestCase):
    def setUp(self):
        trade_columns = pd.Index([TradeField.Ticker, TradeField.StartDate, TradeField.EndDate, TradeField.Return])
        apple_ticker = QuandlTicker("AAPL", "WIKI")
        ibm_ticker = QuandlTicker("IBM", "WIKI")

        self.trades = QFDataFrame(columns=trade_columns, data=[
            [apple_ticker, str_to_date("2015-01-03"), str_to_date("2015-01-10"), 0.1],
            [apple_ticker, str_to_date("2015-02-01"), str_to_date("2015-02-10"), -0.05],
            [apple_ticker, str_to_date("2015-03-01"), str_to_date("2015-03-30"), -0.05],
            [apple_ticker, str_to_date("2015-04-01"), str_to_date("2015-04-30"), 0.1],
            [ibm_ticker, str_to_date("2015-05-01"), str_to_date("2015-05-08"), -0.05],
            [ibm_ticker, str_to_date("2015-06-01"), str_to_date("2015-06-23"), 0.1],
            [ibm_ticker, str_to_date("2015-07-01"), str_to_date("2015-07-30"), -0.05]
        ])

    def test_sqn(self):
        expected_value = 0.178174161
        actual_return = sqn(self.trades)
        self.assertAlmostEqual(expected_value, actual_return, places=4)

    def test_sqn_100_trades(self):
        expected_value = 1.78174161
        actual_return = sqn_for100trades(self.trades)
        self.assertAlmostEqual(expected_value, actual_return, places=4)

    def test_avg_nr_of_trades_per1y(self):
        expected_value = 3.50
        actual_return = avg_nr_of_trades_per1y(self.trades, str_to_date("2015-01-01"), str_to_date("2016-12-31"))
        self.assertAlmostEqual(expected_value, actual_return, places=2)

    def test_trade_based_cagr(self):
        expected_value = 0.041204984
        actual_return = trade_based_cagr(self.trades, str_to_date("2015-01-01"), str_to_date("2016-12-31"))
        self.assertAlmostEqual(expected_value, actual_return, places=4)

    def test_trade_based_max_drawdown(self):
        expected_value = -0.0975
        actual_return = trade_based_max_drawdown(self.trades)
        self.assertAlmostEqual(expected_value, actual_return, places=4)


if __name__ == '__main__':
    unittest.main()
