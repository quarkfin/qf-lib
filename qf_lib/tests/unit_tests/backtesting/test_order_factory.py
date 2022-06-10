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
from math import floor
from unittest.mock import Mock

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.common.tickers.tickers import BloombergTicker, BinanceTicker
from qf_lib.containers.series.qf_series import QFSeries


class TestOrderFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ticker = BloombergTicker('AAPL US Equity')
        cls.crypto_ticker = BinanceTicker('BTC', 'BUSD')
        cls.current_portfolio_value = 1000.0
        cls.share_price = 10.0

        position = Mock(spec=Position)
        position.quantity.return_value = 10.0
        position.ticker.return_value = cls.ticker

        crypto_position = Mock(spec=Position)
        crypto_position.quantity.return_value = 10.0
        crypto_position.ticker.return_value = cls.crypto_ticker

        broker = Mock(spec=Broker)
        broker.get_portfolio_value.return_value = cls.current_portfolio_value
        broker.get_positions.return_value = [position, crypto_position]

        data_handler = Mock(spec=DataHandler)
        data_handler.get_last_available_price.side_effect = lambda tickers, _: \
            QFSeries([cls.share_price] * len(tickers), index=tickers)

        cls.order_factory = OrderFactory(broker, data_handler)

    def test_order(self):
        quantity = 5
        execution_style = MarketOrder()
        time_in_force = TimeInForce.GTC

        orders = self.order_factory.orders({self.ticker: quantity}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, time_in_force))

    def test_order_target(self):
        quantity = -5
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.DAY

        orders = self.order_factory.target_orders({self.ticker: 5}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, time_in_force))

    def test_order_value(self):
        value = 100.0
        quantity = float(floor(100.0 / self.share_price))  # type: float
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.DAY

        orders = self.order_factory.value_orders({self.ticker: value}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, time_in_force))

    def test_order_percent(self):
        percentage = 0.5
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.GTC
        quantity = float(floor(percentage * self.current_portfolio_value / self.share_price))  # type: float

        orders = self.order_factory.percent_orders({self.ticker: percentage}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, time_in_force))

    def test_order_target_value(self):
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.GTC
        quantity = 4

        orders = self.order_factory.target_value_orders({self.ticker: 140.0}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, time_in_force))

    def test_order_target_percent(self):
        quantity = 40
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.GTC

        orders = self.order_factory.target_percent_orders({self.ticker: 0.5}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, time_in_force))

    # Tests for tolerances for target_orders

    def test_order_target_tolerance1(self):
        # there already are 10 shares in the portfolio
        quantity = 11
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.ticker: 2}

        # tolerance is 2 and the difference is 1 -> we should not trade
        orders = self.order_factory.target_orders({self.ticker: quantity}, execution_style, time_in_force, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_tolerance1a(self):
        # there already are 10 shares in the portfolio
        quantity = 100
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.ticker: 91}

        # tolerance is 90 and the difference is 90 -> we should not trade
        orders = self.order_factory.target_orders({self.ticker: quantity}, execution_style, time_in_force, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_tolerance2(self):
        # there already are 10 shares
        quantity = 12
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.ticker: 2}

        # tolerance is 2 and the difference is 2 -> we should not trade
        orders = self.order_factory.target_orders({self.ticker: quantity}, execution_style, time_in_force, tolerance)
        self.assertEqual(orders, [])

    def test_order_target_tolerance3(self):
        # there already are 10 shares
        quantity = 15
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.ticker: 2}

        # tolerance is 2 and the difference is 2 -> we should buy new shares
        orders = self.order_factory.target_orders({self.ticker: quantity}, execution_style, time_in_force, tolerance)
        trade_quantity = 5
        self.assertEqual(orders[0], Order(self.ticker, trade_quantity, execution_style, time_in_force))

    def test_order_target_tolerance3a(self):
        # there already are 10 shares
        quantity = 150
        execution_style = MarketOrder()
        time_in_force = TimeInForce.DAY
        tolerance = {self.ticker: 139}

        # tolerance is 139 and the difference is 140 -> we should buy new shares
        orders = self.order_factory.target_orders({self.ticker: quantity}, execution_style, time_in_force, tolerance)
        trade_quantity = 140
        self.assertEqual(orders[0], Order(self.ticker, trade_quantity, execution_style, time_in_force))

    # Tests for tolerances for target_value_orders

    def test_order_target_value_tolerance1(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 5.0
        target_value = 113.0
        tolerance_percentage = tolerance / target_value

        # tolerance is 5.0$ and the difference is 13$ -> we should buy 1 share
        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = 1
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_value_tolerance2(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 5.0
        target_value = 219.0
        tolerance_percentage = tolerance / target_value

        # tolerance is 5.0$ and the difference is 13$ -> we should buy 1 share
        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = 11
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_value_tolerance3(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 11.0
        target_value = 110.0
        tolerance_percentage = tolerance / target_value

        # tolerance is 11.0$ and the difference is 10$ -> we should not trade
        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        self.assertEqual(orders, [])

    def test_order_target_value_tolerance4(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 11.0
        target_value = 110.999
        tolerance_percentage = tolerance / target_value

        # tolerance is 11.0$ and the difference is 10.999$ -> we should not trade
        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        self.assertEqual(orders, [])

    def test_order_target_value_tolerance5(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 90.1
        tolerance_percentage = tolerance / target_value

        # tolerance is 10.0$ and the difference is 9.9$ -> we should not trade
        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        self.assertEqual(orders, [])

    def test_order_target_value_tolerance6(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 89.9
        tolerance_percentage = tolerance / target_value

        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = -2
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_value_tolerance7(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 9
        target_value = 90.9
        tolerance_percentage = tolerance / target_value

        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = -1
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_value_tolerance8(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.0
        target_value = 45.0
        tolerance_percentage = tolerance / target_value

        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = -6
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_value_tolerance9(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        target_value = 9.0
        tolerance_percentage = 1 / 9

        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = -10
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_value_tolerance10(self):
        # there already are 10 shares price per share is 10 so position value is 100
        execution_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance = 10.99
        target_value = 111.0
        tolerance_percentage = tolerance / target_value

        orders = self.order_factory.target_value_orders({self.ticker: target_value}, execution_style, tif,
                                                        tolerance_percentage)
        quantity = 1
        self.assertEqual(orders[0], Order(self.ticker, quantity, execution_style, tif))

    def test_order_target_percent_tolerance1(self):
        # there are 10 shares price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 1 / 12
        target_value = 0.12

        orders = self.order_factory.target_percent_orders({self.ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        quantity = 2
        self.assertEqual(orders[0], Order(self.ticker, quantity, ex_style, tif))

    def test_crypto_order_target_percent_tolerance1(self):
        # there are 10 shares price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 1 / 12
        target_value = 0.12

        orders = self.order_factory.target_percent_orders({self.crypto_ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        quantity = 2
        self.assertEqual(orders[0], Order(self.crypto_ticker, quantity, ex_style, tif))

    def test_order_target_percent_tolerance2(self):
        # there are 10 shares, price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 1 / 11
        target_value = 0.11

        orders = self.order_factory.target_percent_orders({self.ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        self.assertEqual(orders, [])

    def test_order_target_percent_tolerance3(self):
        # there are 10 shares price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 1 / 9
        target_value = 0.09

        orders = self.order_factory.target_percent_orders({self.ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        self.assertEqual(orders, [])

    def test_order_target_percent_tolerance4(self):
        # there are 10 shares price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 1 / 8
        target_value = 0.08

        orders = self.order_factory.target_percent_orders({self.ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        quantity = -2
        self.assertEqual(orders[0], Order(self.ticker, quantity, ex_style, tif))

    def test_order_target_percent_tolerance5(self):
        # there are 10 shares price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 0.5 / 9
        target_value = 0.09

        orders = self.order_factory.target_percent_orders({self.ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        quantity = -1
        self.assertEqual(orders[0], Order(self.ticker, quantity, ex_style, tif))

    def test_order_target_percent_tolerance6(self):
        # there are 10 shares price per share is 10 so position value is 100
        ex_style = MarketOrder()
        tif = TimeInForce.DAY
        tolerance_percentage = 2 / 50
        target_value = 0.5

        orders = self.order_factory.target_percent_orders({self.ticker: target_value}, ex_style, tif,
                                                          tolerance_percentage)
        quantity = 40
        self.assertEqual(orders[0], Order(self.ticker, quantity, ex_style, tif))

    def test_crypto_order(self):
        quantity = .5
        execution_style = MarketOrder()
        time_in_force = TimeInForce.GTC

        orders = self.order_factory.orders({self.crypto_ticker: quantity}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.crypto_ticker, quantity, execution_style, time_in_force))

    def test_crypto_order_target(self):
        quantity = -4.5
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.DAY

        orders = self.order_factory.target_orders({self.crypto_ticker: 5.5}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.crypto_ticker, quantity, execution_style, time_in_force))

    def test_crypto_order_value(self):
        value = 100.0
        quantity = 100.0 / self.share_price  # type: float
        execution_style = StopOrder(4.20)
        time_in_force = TimeInForce.DAY

        orders = self.order_factory.value_orders({self.crypto_ticker: value}, execution_style, time_in_force)
        self.assertEqual(orders[0], Order(self.crypto_ticker, quantity, execution_style, time_in_force))


if __name__ == "__main__":
    unittest.main()
