import unittest
from typing import Mapping, Sequence

from mockito import mock, when

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import \
    DummyBloombergContractTickerMapper
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder, ExecutionStyle
from qf_lib.backtesting.order.order import Order
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
        cls.contract = Contract(cls.ticker.ticker, 'STK', 'SIM_EXCHANGE')
        cls.initial_risk = 0.02
        position = BrokerPosition(cls.contract, cls.initial_position, 25)

        broker = mock(strict=True)
        when(broker).get_positions().thenReturn([position])

        data_handler = mock(strict=True)
        when(data_handler).get_last_available_price(cls.ticker).thenReturn(110)

        order_factory = _OrderFactoryMock()
        contract_ticker_mapper = DummyBloombergContractTickerMapper()

        cls.simple_position_sizer = SimplePositionSizer(broker, data_handler, order_factory, contract_ticker_mapper)
        cls.initial_risk_position_sizer = InitialRiskPositionSizer(broker, data_handler, order_factory,
                                                                   contract_ticker_mapper, cls.initial_risk)

    def test_simple_position_sizer(self):
        fraction_at_risk = 0.02
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk)
        orders = self.simple_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 2)  # market order and stop order
        self.assertEqual(orders[0], Order(self.contract, Exposure.LONG.value, MarketOrder(), TimeInForce.DAY))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + 1)  # Exposure.LONG.value == 1
        self.assertEqual(orders[1], Order(self.contract, stop_quantity, StopOrder(stop_price), TimeInForce.DAY))

    def test_initial_risk_position_sizer(self):
        fraction_at_risk = 0.01
        signal = Signal(self.ticker, Exposure.LONG, fraction_at_risk)
        orders = self.initial_risk_position_sizer.size_signals([signal])

        self.assertEqual(len(orders), 2)  # market order and stop order
        additional_contracts = self.initial_risk / fraction_at_risk
        self.assertEqual(orders[0], Order(self.contract, additional_contracts, MarketOrder(), TimeInForce.DAY))

        stop_price = self.last_price * (1 - fraction_at_risk)
        stop_quantity = -(self.initial_position + additional_contracts)
        self.assertEqual(orders[1], Order(self.contract, stop_quantity, StopOrder(stop_price), TimeInForce.DAY))


class _OrderFactoryMock(object):
    def target_percent_orders(self, target_quantities: Mapping[Contract, float], execution_style,
                              time_in_force=TimeInForce.DAY) -> Sequence[Order]:
        contract, target_percentage = next(iter(target_quantities.items()))
        # target percentage is passed as order quantity -> just to make the testing easy
        return [Order(contract, target_percentage, execution_style, time_in_force)]

    def orders(self, quantities: Mapping[Contract, int], execution_style: ExecutionStyle,
               time_in_force: TimeInForce = TimeInForce.DAY) -> Sequence[Order]:

        contract, quantity = next(iter(quantities.items()))
        return [Order(contract, quantity, execution_style, time_in_force)]

if __name__ == "__main__":
    unittest.main()
