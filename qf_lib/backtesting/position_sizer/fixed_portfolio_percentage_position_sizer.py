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

from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer


class FixedPortfolioPercentagePositionSizer(PositionSizer):
    """
    This PositionSizer converts signals to orders using Fixed Percentage value.
    Each signal will be sized based on that percentage of the portfolio.
    """

    def __init__(self, broker: Broker, data_handler: DataHandler, order_factory: OrderFactory,
                 contract_ticker_mapper: ContractTickerMapper, fixed_percentage: float):
        """
        fixed_percentage - should be set once for all signals. It corresponds to the fraction of a portfolio that we
        are investing in every asset on single trade.
        For example: fixed_percentage = 0.2, means that we are investing 20% of portfolio to
        any signal that is long or short.
        """
        super().__init__(broker, data_handler, order_factory, contract_ticker_mapper)

        self.fixed_percentage = fixed_percentage

    def _generate_market_order(self, contract, signal: Signal) -> Order:
        target_percentage = signal.suggested_exposure.value * self.fixed_percentage

        market_order_list = self._order_factory.target_percent_orders(
            {contract: target_percentage}, MarketOrder(), TimeInForce.OPG)
        if len(market_order_list) == 0:
            return None

        assert len(market_order_list) == 1, "Only one order should be generated"
        return market_order_list[0]
