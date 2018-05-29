import unittest

import pandas as pd
from mockito import mock, when

from qf_lib.backtesting.qstrader.order.orderfactory import OrderFactory
from qf_lib.common.tickers.tickers import BloombergTicker


class TestOrderFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ticker = BloombergTicker('AAPL US Equity')
        cls.current_portfolio_value = 1000.0
        cls.share_price = 10.0

        portfolio = mock({'current_portfolio_value': cls.current_portfolio_value}, strict=True)
        position = mock({'number_of_shares': 10}, strict=True)
        when(portfolio).get_position(cls.ticker).thenReturn(position)

        data_handler = mock(strict=True)
        when(data_handler).get_last_available_price([cls.ticker]).thenReturn(
            pd.Series([cls.share_price], index=[cls.ticker]))
        cls.order_factory = OrderFactory(portfolio, data_handler)

    def test_order(self):
        quantity = 5
        orders = self.order_factory.orders({self.ticker: quantity})
        self.assertEqual(orders[0].quantity, quantity)
        self.assertEqual(orders[0].ticker, self.ticker)

    def test_order_target(self):
        orders = self.order_factory.target_orders({self.ticker: 5})
        self.assertEqual(orders[0].ticker, self.ticker)
        self.assertEqual(orders[0].quantity, -5)

    def test_order_value(self):
        orders = self.order_factory.value_orders({self.ticker: 100.0})
        self.assertEqual(orders[0].ticker, self.ticker)
        self.assertEqual(orders[0].quantity, 100.0/self.share_price)

    def test_order_percent(self):
        percentage = 0.5
        orders = self.order_factory.percent_order({self.ticker: percentage})
        self.assertEqual(orders[0].ticker, self.ticker)
        self.assertEqual(orders[0].quantity, percentage * self.current_portfolio_value / self.share_price)

    def test_order_target_value(self):
        orders = self.order_factory.target_value_order({self.ticker: 140.0})
        self.assertEqual(orders[0].ticker, self.ticker)
        self.assertEqual(orders[0].quantity, 4)

    def test_order_target_percent(self):
        orders = self.order_factory.order_target_percent({self.ticker: 0.5})
        self.assertEqual(orders[0].ticker, self.ticker)
        self.assertEqual(orders[0].quantity, 40)


if __name__ == "__main__":
    unittest.main()
