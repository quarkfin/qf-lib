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
from typing import Mapping, Sequence

import numpy as np
from mockito import mock, when

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder, ExecutionStyle
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.broker_positon import BrokerPosition
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.common.tickers.tickers import BloombergTicker


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

        broker = mock(strict=True)
        when(broker).get_positions().thenReturn([position])

        data_handler = mock(strict=True)
        when(data_handler).get_last_available_price(cls.ticker).thenReturn(110)

        order_factory = _OrderFactoryMock(cls.initial_position, cls.initial_allocation)  # type: OrderFactory
        contract_ticker_mapper = DummyBloombergContractTickerMapper()

        cls.simple_position_sizer = SimplePositionSizer(broker, data_handler, order_factory, contract_ticker_mapper)
        cls.initial_risk_position_sizer = InitialRiskPositionSizer(broker, data_handler, order_factory,
                                                                   contract_ticker_mapper, cls.initial_risk,
                                                                   cls.max_target_percentage)

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


class _OrderFactoryMock(object):

    def __init__(self, initial_position: int, initial_allocation: float):
        self.initial_position = initial_position
        self.initial_allocation = initial_allocation

    def target_percent_orders(self, target_percentages: Mapping[Contract, float], execution_style,
                              time_in_force=TimeInForce.DAY, tolerance_percent=0.0) -> Sequence[Order]:
        contract, target_percentage = next(iter(target_percentages.items()))
        order_quantity = int(np.floor(self.initial_position * (target_percentage / self.initial_allocation - 1)))
        return [Order(contract, order_quantity, execution_style, time_in_force)]

    def orders(self, quantities: Mapping[Contract, int], execution_style: ExecutionStyle,
               time_in_force: TimeInForce = TimeInForce.DAY) -> Sequence[Order]:
        order_list = []
        for contract, quantity in quantities.items():
            if quantity != 0:
                order_list.append(Order(contract, quantity, execution_style, time_in_force))
        return order_list


if __name__ == "__main__":
    unittest.main()
