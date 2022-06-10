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
from typing import Sequence
from unittest.mock import Mock

import numpy as np

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.position_sizer.initial_risk_with_volume_position_sizer import InitialRiskWithVolumePositionSizer
from qf_lib.backtesting.signals.backtest_signals_register import BacktestSignalsRegister
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.broker_positon import BrokerPosition
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.common.tickers.tickers import BloombergTicker, BinanceTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.qf_series import QFSeries


class TestPositionSizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ticker = BloombergTicker('AAPL US Equity')
        cls.crypto_ticker = BinanceTicker('BTC', 'BUSD')
        cls.last_price = 110
        cls.initial_position = 200
        cls.initial_allocation = 0.5  # 50% of our portfolio is invested in AAPL
        cls.initial_risk = 0.02
        cls.max_target_percentage = 1.5
        cls.portfolio_value = 1000
        cls.volume = QFSeries([1.5 for i in range(10)])

    def setUp(self) -> None:
        position = BrokerPosition(self.ticker, self.initial_position, 25)
        crypto_position = BrokerPosition(self.crypto_ticker, self.initial_position, 25)

        self.timer = Mock(spec=Timer)
        self.timer.now.return_value = str_to_date("2017-01-01")

        self.broker = Mock(spec=Broker)
        self.broker.get_open_orders.return_value = []
        self.broker.get_positions.return_value = [position, crypto_position]
        self.broker.get_portfolio_value.return_value = self.portfolio_value

        data_handler = Mock(spec=DataHandler, timer=self.timer)
        data_handler.get_last_available_price.side_effect = lambda _: self.last_price
        data_handler.get_price.return_value = self.volume

        order_factory = self._mock_order_factory(self.initial_position, self.initial_allocation)

        self.simple_position_sizer = SimplePositionSizer(self.broker, data_handler, order_factory,
                                                         BacktestSignalsRegister())

        self.initial_risk_position_sizer = InitialRiskPositionSizer(self.broker, data_handler, order_factory,
                                                                    BacktestSignalsRegister(),
                                                                    self.initial_risk,
                                                                    self.max_target_percentage)

        self.initial_risk_with_volume_position_sizer = InitialRiskWithVolumePositionSizer(self.broker, data_handler,
                                                                                          order_factory, BacktestSignalsRegister(),
                                                                                          self.initial_risk, self.max_target_percentage)

    @classmethod
    def _mock_order_factory(cls, initial_position, initial_allocation):
        def target_percent_orders(target_percentages, execution_style, time_in_force, tolerance_percentage=0.0,
                                  frequency=None):
            return [Order(contract, float(np.floor(initial_position * (target_percentage / initial_allocation - 1))),
                          execution_style, time_in_force) for contract, target_percentage in target_percentages.items()]

        def orders(quantities, execution_style, time_in_force) -> Sequence[Order]:
            return [Order(contract, quantity, execution_style, time_in_force)
                    for contract, quantity in quantities.items()]

        def target_value_orders(quantities, execution_style, time_in_force, tolerance_quantities=0.0, frequency=None) -> Sequence[Order]:
            return [Order(ticker, quantity, execution_style, time_in_force) for ticker, quantity in quantities.items()]

        order_factory = Mock(spec=OrderFactory)

        order_factory.orders.side_effect = orders
        order_factory.target_percent_orders.side_effect = target_percent_orders
        order_factory.target_value_orders.side_effect = target_value_orders

        return order_factory

    def test_simple_position_sizer(self):
        fraction_at_risk = 0.02
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = self.simple_position_sizer.size_signals([signal])

        quantity = float(np.floor(self.initial_position * (1 / self.initial_allocation - 1)))
        self.assertEqual(len(orders), 2)  # market order and stop order
        self.assertEqual(orders[0], Order(self.ticker, quantity, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + quantity)
        self.assertEqual(orders[1], Order(self.ticker, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_initial_risk_position_sizer_with_cap(self):
        """
        Max leverage will be limited by position sizer to 1.5
        """
        fraction_at_risk = 0.01  # will give leverage of 2, that will be capped to 1.5
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = self.initial_risk_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 2)  # market order and stop order
        portfolio_value = self.initial_position / self.initial_allocation
        max_leverage = self.initial_risk_position_sizer.max_target_percentage
        target_quantity = float(np.floor(portfolio_value * max_leverage))
        additional_contracts = target_quantity - self.initial_position
        self.assertEqual(orders[0], Order(self.ticker, additional_contracts, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + additional_contracts)
        self.assertEqual(orders[1], Order(self.ticker, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_initial_risk_position_sizer_without_cap(self):
        """
        Max leverage will not be limited by position sizer
        """
        fraction_at_risk = 0.23
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = self.initial_risk_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 2)  # market order and stop order
        portfolio_value = self.initial_position / self.initial_allocation
        target_quantity = float(np.floor(portfolio_value * self.initial_risk / fraction_at_risk))
        additional_contracts = target_quantity - self.initial_position
        self.assertEqual(orders[0], Order(self.ticker, additional_contracts, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + additional_contracts)
        self.assertEqual(orders[1], Order(self.ticker, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_out_signal(self):
        fraction_at_risk = 0.02
        signal = Signal(self.ticker, Exposure.OUT, fraction_at_risk, self.last_price, self.timer.now())
        orders = self.simple_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 1)  # market order only
        self.assertEqual(orders[0], Order(self.ticker, -200, MarketOrder(), TimeInForce.OPG))

    def test_decreasing_stop_price__with_open_positions(self):
        """
        Tests if the stop price of consecutive StopOrders, created for a single position, can decrease over time.
        The PositionSizer + Broker setup should not allow this situation to happen.
        """
        position_sizer = self.simple_position_sizer
        self.broker.get_open_orders.return_value = []

        # Set the last available price to 100, fraction_at_risk to 0.1, stop price would be in this case
        # equal to 100 * (1 - 0.1) = 90
        self.timer.now.return_value = str_to_date("2017-01-01") + RelativeDelta(hours=7)
        self.last_price = 100
        fraction_at_risk = 0.1
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = position_sizer.size_signals([signal], use_stop_losses=True)
        stop_order_1 = [o for o in orders if isinstance(o.execution_style, StopOrder)][0]

        # Simulate placing the orders - broker should return them as open orders
        self.broker.get_open_orders.return_value = orders

        # Simulate next day price change to a price above the previous stop_price - StopOrder is not triggered
        self.last_price = 91

        # Size signals once again (the next day). The new StopOrder stop price should not be lower than the
        # previous one (90)
        self.timer.now.return_value = str_to_date("2017-01-02") + RelativeDelta(hours=7)
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = position_sizer.size_signals([signal], use_stop_losses=True)

        stop_order_2 = [o for o in orders if isinstance(o.execution_style, StopOrder)][0]
        self.assertTrue(stop_order_1.execution_style.stop_price == stop_order_2.execution_style.stop_price)

    def test_decreasing_stop_price__no_open_positions(self):
        """
        Tests if the stop price of consecutive StopOrders, created for a single position, can decrease over time.
        The PositionSizer + Broker setup should allow this situation to happen in case if there is no open position
        for the given contract.
        """
        position_sizer = self.simple_position_sizer
        self.broker.get_positions.return_value = []

        # Set the last available price to 100, fraction_at_risk to 0.1, stop price would be in this case
        # equal to 100 * (1 - 0.1) = 90
        self.last_price = 100
        fraction_at_risk = 0.1
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = position_sizer.size_signals([signal], use_stop_losses=True)
        stop_order_1 = [o for o in orders if isinstance(o.execution_style, StopOrder)][0]

        # Simulate placing the orders - broker should return them as open orders
        self.broker.get_open_orders.return_value = orders

        # Simulate next day price change to a price above the previous stop_price - StopOrder is not triggered
        self.last_price = 91

        # Size signals once again (the next day). The new StopOrder stop price should not be lower than the
        # previous one (90)
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = position_sizer.size_signals([signal], use_stop_losses=True)

        stop_order_2 = [o for o in orders if isinstance(o.execution_style, StopOrder)][0]
        self.assertTrue(stop_order_1.execution_style.stop_price > stop_order_2.execution_style.stop_price)

    def test_simple_initial_risk_with_volume_position_sizer(self):
        fraction_at_risk = 0.02
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = self.initial_risk_with_volume_position_sizer.size_signals([signal])

        quantity = (self.portfolio_value * self.initial_risk_with_volume_position_sizer.max_target_percentage) / (self.last_price * self.ticker.point_value)
        divisor = self.last_price * self.ticker.point_value
        target_quantity = float(np.floor(self.volume.mean() * self.initial_risk_with_volume_position_sizer._max_volume_percentage) * divisor * np.sign(quantity))
        self.assertEqual(len(orders), 2)  # market order and stop order
        self.assertEqual(orders[0], Order(self.ticker, target_quantity, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + target_quantity)
        self.assertEqual(orders[1], Order(self.ticker, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_simple_crypto_initial_risk_with_volume_position_sizer(self):
        fraction_at_risk = 0.02
        signal = Signal(self.crypto_ticker, Exposure.LONG, fraction_at_risk, self.last_price, self.timer.now())
        orders = self.initial_risk_with_volume_position_sizer.size_signals([signal])

        quantity = (self.portfolio_value * self.initial_risk_with_volume_position_sizer.max_target_percentage) / (self.last_price * self.ticker.point_value)
        divisor = self.last_price * self.ticker.point_value
        target_quantity = self.volume.mean() * self.initial_risk_with_volume_position_sizer._max_volume_percentage * divisor * np.sign(quantity)
        self.assertEqual(len(orders), 2)  # market order and stop order
        self.assertEqual(orders[0], Order(self.crypto_ticker, target_quantity, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + target_quantity)
        self.assertEqual(orders[1], Order(self.crypto_ticker, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))


if __name__ == "__main__":
    unittest.main()
