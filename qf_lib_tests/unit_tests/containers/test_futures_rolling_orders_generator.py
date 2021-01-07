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
from unittest import mock
from unittest.mock import MagicMock

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.simulated_bloomberg_mapper import \
    SimulatedBloombergContractTickerMapper
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.futures_rolling_orders_generator import FuturesRollingOrdersGenerator
from qf_lib.containers.series.qf_series import QFSeries


@mock.patch('qf_lib.backtesting.broker.broker.Broker', autospec=True)
@mock.patch('qf_lib.backtesting.order.order_factory.OrderFactory', autospec=True)
@mock.patch('qf_lib.containers.futures.future_tickers.future_ticker.FutureTicker', autospec=True)
class TestFuturesRollingOrdersGenerator(unittest.TestCase):

    def setUp(self) -> None:
        self.contract_ticker_mapper = SimulatedBloombergContractTickerMapper()
        self.current_date = str_to_date("2017-01-01")

        self.timer = SettableTimer(self.current_date)

    def test_generate_close_orders__no_orders_close(self, future_ticker, order_factory, broker):
        """
        Test if the FuturesRollingOrdersGenerator does not close positions for contracts which are still valid.
        """
        contract_in_portfolio = Contract("CLG01 Comdty", "FUT", "SIM_EXCHANGE")
        broker.get_positions.return_value = [BacktestPositionFactory.create_position(contract_in_portfolio)]

        future_ticker.get_current_specific_ticker.return_value = BloombergTicker("CLG01 Comdty")
        rolling_orders_generator = FuturesRollingOrdersGenerator([future_ticker], self.timer, broker, order_factory,
                                                                 self.contract_ticker_mapper)
        rolling_orders_generator.generate_close_orders()
        order_factory.target_percent_orders.assert_not_called()

    def test_generate_close_orders__multiple_orders_close(self, future_ticker, order_factory, broker):
        """
        There exist positions open in the portfolio for tickers, which belong to the same family as the
        future_ticker.

        Test if the order factory will be called with the necessary function and parameters to close the existing
        positions and if any errors have been logged (as the expiration dates did not occur, no logs should be
        generated).
        """
        # Make the broker return positions with contracts_in_portfolio from the get_positions function
        contracts_in_portfolio = [Contract("CLG00 Comdty", "FUT", "SIM_EXCHANGE"),
                                  Contract("CLN00 Comdty", "FUT", "SIM_EXCHANGE")]
        broker.get_positions.side_effect = lambda: [BacktestPositionFactory.create_position(c)
                                                    for c in contracts_in_portfolio]

        # Set current ticker to be different then any ticker from expired_contracts
        future_ticker.get_current_specific_ticker.return_value = BloombergTicker("CLG01 Comdty")
        future_ticker.belongs_to_family.return_value = True
        future_ticker.get_expiration_dates.return_value = QFSeries(data=[BloombergTicker("CLG00 Comdty"),
                                                                         BloombergTicker("CLN00 Comdty")],
                                                                   index=[self.current_date - RelativeDelta(days=10),
                                                                          self.current_date + RelativeDelta(days=5)])

        rolling_orders_generator = FuturesRollingOrdersGenerator([future_ticker], self.timer, broker, order_factory,
                                                                 self.contract_ticker_mapper)
        rolling_orders_generator.logger = MagicMock()
        rolling_orders_generator.generate_close_orders()

        # The order factory should be called exactly once and in should contain all contracts from
        # contracts_in_portfolio
        order_factory.target_percent_orders.assert_called_once_with(
            {c: 0 for c in contracts_in_portfolio}, MarketOrder(), TimeInForce.GTC
        )
        # The logger error function should be called only once, as only expiration date of one of the contracts in the
        # portfolio already passed
        rolling_orders_generator.logger.error.assert_called_once()

    def test_generate_close_orders__current_ticker_in_portfolio(self, future_ticker, order_factory, broker):
        """
        There exist positions open in the portfolio for tickers, which belong to the same family as the
        future_ticker and for the current ticker.

        Test if only the expired contracts will be closed.
        """
        expired_contract = Contract("CLG00 Comdty", "FUT", "SIM_EXCHANGE")
        current_contract = Contract("CLG01 Comdty", "FUT", "SIM_EXCHANGE")
        contracts_in_portfolio = [expired_contract, current_contract]
        broker.get_positions.side_effect = lambda: [BacktestPositionFactory.create_position(c)
                                                    for c in contracts_in_portfolio]

        # Set current ticker to be different then ticker corresponding to expired_contract
        future_ticker.get_current_specific_ticker.return_value = BloombergTicker("CLG01 Comdty")
        future_ticker.belongs_to_family.return_value = True
        future_ticker.get_expiration_dates.return_value = QFSeries(data=[BloombergTicker("CLG00 Comdty"),
                                                                         BloombergTicker("CLG01 Comdty")],
                                                                   index=[self.current_date + RelativeDelta(days=1),
                                                                          self.current_date + RelativeDelta(days=5)])

        rolling_orders_generator = FuturesRollingOrdersGenerator([future_ticker], self.timer, broker, order_factory,
                                                                 self.contract_ticker_mapper)
        rolling_orders_generator.logger = MagicMock()
        rolling_orders_generator.generate_close_orders()

        # The order factory should be called exactly once and in should contain all contracts from
        # contracts_in_portfolio
        order_factory.target_percent_orders.assert_called_once_with(
            {expired_contract: 0}, MarketOrder(), TimeInForce.GTC
        )
        # The logger error function should not have been called
        rolling_orders_generator.logger.error.assert_not_called()

    def test_generate_close_orders__multiple_future_tickers(self, future_ticker, order_factory, broker):
        contracts_in_portfolio = [Contract("CLG00 Comdty", "FUT", "SIM_EXCHANGE"),
                                  Contract("CLG01 Comdty", "FUT", "SIM_EXCHANGE")]
        specific_tickers = [BloombergTicker("CLG00 Comdty"), BloombergTicker("CLG01 Comdty")]

        contracts_in_portfolio_2 = [Contract("CTG00 Comdty", "FUT", "SIM_EXCHANGE"),
                                    Contract("CTG01 Comdty", "FUT", "SIM_EXCHANGE")]
        specific_tickers_2 = [BloombergTicker("CTG00 Comdty"), BloombergTicker("CTG01 Comdty")]

        broker.get_positions.side_effect = lambda: [BacktestPositionFactory.create_position(c)
                                                    for c in contracts_in_portfolio + contracts_in_portfolio_2]

        # Generate the FuturesRollingOrdersGenerator for two different Future Tickers
        future_ticker.get_current_specific_ticker.return_value = BloombergTicker("CLG01 Comdty")
        future_ticker.belongs_to_family.side_effect = lambda t: t in specific_tickers
        future_ticker.get_expiration_dates.return_value = QFSeries(data=specific_tickers,
                                                                   index=[self.current_date - RelativeDelta(days=10),
                                                                          self.current_date + RelativeDelta(days=5)])
        future_ticker2 = MagicMock()
        future_ticker2.get_current_specific_ticker.return_value = BloombergTicker("CTG01 Comdty")
        future_ticker2.belongs_to_family.side_effect = lambda t: t in specific_tickers_2
        future_ticker2.get_expiration_dates.return_value = QFSeries(data=specific_tickers_2,
                                                                    index=[self.current_date - RelativeDelta(days=10),
                                                                           self.current_date + RelativeDelta(days=5)])

        rolling_orders_generator = FuturesRollingOrdersGenerator([future_ticker, future_ticker2], self.timer, broker,
                                                                 order_factory, self.contract_ticker_mapper)
        rolling_orders_generator.logger = MagicMock()
        rolling_orders_generator.generate_close_orders()

        order_factory.target_percent_orders.assert_called_once_with(
            {Contract("CLG00 Comdty", "FUT", "SIM_EXCHANGE"): 0,
             Contract("CTG00 Comdty", "FUT", "SIM_EXCHANGE"): 0}, MarketOrder(), TimeInForce.GTC
        )

    def test_generate_close_orders__no_valid_ticker(self, future_ticker, order_factory, broker):
        """
        There exist a position open in the portfolio for tickers, which belong to the same family as the
        future_ticker. Currently there is no valid ticker for the FutureTicker, which means the contract
        corresponding to the open position expired and the position should be closed.
        """
        contract_in_portfolio = Contract("CLG00 Comdty", "FUT", "SIM_EXCHANGE")
        broker.get_positions.return_value = [BacktestPositionFactory.create_position(contract_in_portfolio)]

        # No valid ticker currently exists for the future ticker
        future_ticker.get_current_specific_ticker.side_effect = NoValidTickerException()
        future_ticker.belongs_to_family.return_value = True
        future_ticker.get_expiration_dates.return_value = QFSeries(data=[BloombergTicker("CLG00 Comdty")],
                                                                   index=[self.current_date - RelativeDelta(days=10)])

        rolling_orders_generator = FuturesRollingOrdersGenerator([future_ticker], self.timer, broker, order_factory,
                                                                 self.contract_ticker_mapper)
        rolling_orders_generator.generate_close_orders()

        # The order factory should be called exactly once and in should contain all contracts from
        # contracts_in_portfolio
        order_factory.target_percent_orders.assert_called_once_with(
            {contract_in_portfolio: 0}, MarketOrder(), TimeInForce.GTC
        )
