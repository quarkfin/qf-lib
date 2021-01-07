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
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.simulated_bloomberg_mapper import \
    SimulatedBloombergContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.monitoring.signals_register import SignalsRegister
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.broker_positon import BrokerPosition
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import Timer


class TestPositionSizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ticker = BloombergTicker('AAPL US Equity')
        cls.last_price = 110
        cls.initial_position = 200
        cls.initial_allocation = 0.5  # 50% of our portfolio is invested in AAPL
        cls.contract = Contract(cls.ticker.ticker, 'STK', 'SIM_EXCHANGE')
        cls.initial_risk = 0.02
        cls.max_target_percentage = 1.5
        position = BrokerPosition(cls.contract, cls.initial_position, 25)

        timer = Mock(spec=Timer)
        timer.now.return_value = str_to_date("2017-01-01")

        broker = Mock(spec=Broker)
        broker.get_positions.return_value = [position]

        data_handler = Mock(spec=DataHandler, timer=timer)
        data_handler.get_last_available_price.return_value = cls.last_price

        order_factory = cls._mock_order_factory(cls.initial_position, cls.initial_allocation)
        contract_ticker_mapper = SimulatedBloombergContractTickerMapper()

        cls.simple_position_sizer = SimplePositionSizer(broker, data_handler, order_factory, contract_ticker_mapper,
                                                        SignalsRegister())
        cls.initial_risk_position_sizer = InitialRiskPositionSizer(broker, data_handler, order_factory,
                                                                   contract_ticker_mapper,
                                                                   SignalsRegister(),
                                                                   cls.initial_risk,
                                                                   cls.max_target_percentage)

    @classmethod
    def _mock_order_factory(cls, initial_position, initial_allocation):

        def target_percent_orders(target_percentages, execution_style, time_in_force, tolerance_percentage=0.0):
            return [Order(contract, np.floor(initial_position * (target_percentage / initial_allocation - 1)),
                          execution_style, time_in_force) for contract, target_percentage in target_percentages.items()]

        def orders(quantities, execution_style, time_in_force) -> Sequence[Order]:
            return [Order(contract, quantity, execution_style, time_in_force)
                    for contract, quantity in quantities.items()]

        order_factory = Mock(spec=OrderFactory)

        order_factory.orders.side_effect = orders
        order_factory.target_percent_orders.side_effect = target_percent_orders

        return order_factory

    def test_simple_position_sizer(self):
        fraction_at_risk = 0.02
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk)
        orders = self.simple_position_sizer.size_signals([signal])

        quantity = np.floor(self.initial_position * (1 / self.initial_allocation - 1))
        self.assertEqual(len(orders), 2)  # market order and stop order
        self.assertEqual(orders[0], Order(self.contract, quantity, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + quantity)
        self.assertEqual(orders[1], Order(self.contract, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_initial_risk_position_sizer_with_cap(self):
        """
        Max leverage will be limited by position sizer to 1.5
        """
        fraction_at_risk = 0.01   # will give leverage of 2, that will be capped to 1.5
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk)
        orders = self.initial_risk_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 2)  # market order and stop order
        portfolio_value = self.initial_position / self.initial_allocation
        max_leverage = self.initial_risk_position_sizer.max_target_percentage
        target_quantity = int(np.floor(portfolio_value * max_leverage))
        additional_contracts = target_quantity - self.initial_position
        self.assertEqual(orders[0], Order(self.contract, additional_contracts, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + additional_contracts)
        self.assertEqual(orders[1], Order(self.contract, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_initial_risk_position_sizer_without_cap(self):
        """
        Max leverage will not be limited by position sizer
        """
        fraction_at_risk = 0.23
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk)
        orders = self.initial_risk_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 2)  # market order and stop order
        portfolio_value = self.initial_position / self.initial_allocation
        target_quantity = int(np.floor(portfolio_value * self.initial_risk / fraction_at_risk))
        additional_contracts = target_quantity - self.initial_position
        self.assertEqual(orders[0], Order(self.contract, additional_contracts, MarketOrder(), TimeInForce.OPG))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + additional_contracts)
        self.assertEqual(orders[1], Order(self.contract, stop_quantity, StopOrder(stop_price), TimeInForce.GTC))

    def test_out_signal(self):
        fraction_at_risk = 0.02
        signal = Signal(self.ticker, Exposure.OUT, fraction_at_risk)
        orders = self.simple_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 1)  # market order only
        self.assertEqual(orders[0], Order(self.contract, -200, MarketOrder(), TimeInForce.OPG))


if __name__ == "__main__":
    unittest.main()
