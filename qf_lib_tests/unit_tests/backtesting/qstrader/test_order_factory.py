import unittest
from math import floor

import pandas as pd
from mockito import mock, when

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import \
    DummyBloombergContractTickerMapper
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.tickers.tickers import BloombergTicker


class TestOrderFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = Contract('AAPL US Equity', 'STK', 'NASDAQ')
        cls.ticker = BloombergTicker('AAPL US Equity')
        cls.current_portfolio_value = 1000.0
        cls.share_price = 10.0

        position = mock(strict=True)
        when(position).quantity().thenReturn(10)
        when(position).contract().thenReturn(cls.contract)

        broker = mock(strict=True)
        when(broker).get_portfolio_value().thenReturn(cls.current_portfolio_value)
        when(broker).get_positions().thenReturn([position])

        data_handler = mock(strict=True)
        when(data_handler).get_last_available_price([cls.ticker]).thenReturn(
            pd.Series([cls.share_price], index=[cls.ticker]))

        cls.order_factory = OrderFactory(broker, data_handler, DummyBloombergContractTickerMapper())

    def test_order(self):
        quantity = 5
        execution_style = MarketOrder()
        time_in_force = TimeInForce.GTC

        orders = self.order_factory.orders({self.contract: quantity}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, time_in_force))

    def test_order_target(self):
        quantity = -5
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.DAY

        orders = self.order_factory.target_orders({self.contract: 5}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, time_in_force))

    def test_order_value(self):
        value = 100.0
        quantity = floor(100.0/self.share_price)  # type: int
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.DAY

        orders = self.order_factory.value_orders({self.contract: value}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, time_in_force))

    def test_order_percent(self):
        percentage = 0.5
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.GTC
        quantity = floor(percentage * self.current_portfolio_value / self.share_price)  # type: int

        orders = self.order_factory.percent_orders({self.contract: percentage}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, time_in_force))

    def test_order_target_value(self):
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.GTC
        quantity = 4

        orders = self.order_factory.target_value_orders({self.contract: 140.0}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, time_in_force))

    def test_order_target_percent(self):
        quantity = 40
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.GTC

        orders = self.order_factory.target_percent_orders({self.contract: 0.5}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, time_in_force))

    # Tests for tolerances for target_orders

    def test_order_target_tolerance1(self):
        # there already are 10 shares in the portfolio
        quantity = 11
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.contract: 2}

        # tolerance is 2 and the difference is 1 -> we should not trade
        orders = self.order_factory.target_orders({self.contract: quantity}, execution_style, time_in_force, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_tolerance1a(self):
        # there already are 10 shares in the portfolio
        quantity = 100
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.contract: 91}

        # tolerance is 90 and the difference is 90 -> we should not trade
        orders = self.order_factory.target_orders({self.contract: quantity}, execution_style, time_in_force, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_tolerance2(self):
        # there already are 10 shares
        quantity = 12
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.contract: 2}

        # tolerance is 2 and the difference is 2 -> we should not trade
        orders = self.order_factory.target_orders({self.contract: quantity}, execution_style, time_in_force, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_tolerance3(self):
        # there already are 10 shares
        quantity = 15
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.contract: 2}

        # tolerance is 2 and the difference is 2 -> we should buy new shares
        orders = self.order_factory.target_orders({self.contract: quantity}, execution_style, time_in_force, tolerance)
        trade_quantity = 5
        self.assertEqual(orders[0], Order(self.contract, trade_quantity, execution_style, time_in_force))

    def test_order_target_tolerance3a(self):
        # there already are 10 shares
        quantity = 150
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.contract: 139}

        # tolerance is 139 and the difference is 140 -> we should buy new shares
        orders = self.order_factory.target_orders({self.contract: quantity}, execution_style, time_in_force, tolerance)
        trade_quantity = 140
        self.assertEqual(orders[0], Order(self.contract, trade_quantity, execution_style, time_in_force))

    # Tests for tolerances for target_value_orders

    def test_order_target_value_tolerance1(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 5.0
        target_value = 113.0

        # tolerance is 5.0$ and the difference is 13$ -> we should buy 1 share
        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = 1
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_value_tolerance2(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 5.0
        target_value = 219.0

        # tolerance is 5.0$ and the difference is 13$ -> we should buy 1 share
        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = 11
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_value_tolerance3(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 11.0
        target_value = 110.0

        # tolerance is 11.0$ and the difference is 10$ -> we should not trade
        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_value_tolerance4(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 11.0
        target_value = 110.999

        # tolerance is 11.0$ and the difference is 10.999$ -> we should not trade
        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_value_tolerance5(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 90.1

        # tolerance is 10.0$ and the difference is 9.9$ -> we should not trade
        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_value_tolerance6(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 89.9

        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = -2
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_value_tolerance7(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 9
        target_value = 90.9

        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = -1
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_value_tolerance8(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 45.0

        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = -6
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_value_tolerance9(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 9.0

        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = -10
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_value_tolerance10(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.99
        target_value = 111.0

        orders = self.order_factory.target_value_orders({self.contract: target_value}, execution_style, tif, tolerance)
        quantity = 1
        self.assertEqual(orders[0], Order(self.contract, quantity, execution_style, tif))

    def test_order_target_percent_tolerance1(self):
        # there are 10 shares price per share is 10 so position value is 100, it corresponds to 10% of portfolio
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 0.01
        target_value = 0.12

        orders = self.order_factory.target_percent_orders({self.contract: target_value}, ex_style, tif, tolerance)
        quantity = 2
        self.assertEqual(orders[0], Order(self.contract, quantity, ex_style, tif))

    def test_order_target_percent_tolerance2(self):
        # there are 10 shares price per share is 10 so position value is 100, it corresponds to 10% of portfolio
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 0.01
        target_value = 0.11

        orders = self.order_factory.target_percent_orders({self.contract: target_value}, ex_style, tif, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_percent_tolerance3(self):
        # there are 10 shares price per share is 10 so position value is 100, it corresponds to 10% of portfolio
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 0.01
        target_value = 0.09

        orders = self.order_factory.target_percent_orders({self.contract: target_value}, ex_style, tif, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_percent_tolerance4(self):
        # there are 10 shares price per share is 10 so position value is 100, it corresponds to 10% of portfolio
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 0.01
        target_value = 0.08

        orders = self.order_factory.target_percent_orders({self.contract: target_value}, ex_style, tif, tolerance)
        quantity = -2
        self.assertEqual(orders[0], Order(self.contract, quantity, ex_style, tif))

    def test_order_target_percent_tolerance5(self):
        # there are 10 shares price per share is 10 so position value is 100, it corresponds to 10% of portfolio
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 0.005
        target_value = 0.09

        orders = self.order_factory.target_percent_orders({self.contract: target_value}, ex_style, tif, tolerance)
        quantity = -1
        self.assertEqual(orders[0], Order(self.contract, quantity, ex_style, tif))

    def test_order_target_percent_tolerance6(self):
        # there are 10 shares price per share is 10 so position value is 100, it corresponds to 10% of portfolio
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 0.02
        target_value = 0.5

        orders = self.order_factory.target_percent_orders({self.contract: target_value}, ex_style, tif, tolerance)
        quantity = 40
        self.assertEqual(orders[0], Order(self.contract, quantity, ex_style, tif))


if __name__ == "__main__":
    unittest.main()
