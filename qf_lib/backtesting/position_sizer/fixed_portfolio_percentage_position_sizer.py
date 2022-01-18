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
from typing import Optional, List

from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.signals.signals_register import SignalsRegister
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.common.enums.frequency import Frequency
from qf_lib.data_providers.data_provider import DataProvider


class FixedPortfolioPercentagePositionSizer(PositionSizer):
    """
    This PositionSizer converts signals to orders using Fixed Percentage value.
    Each signal will be sized based on that percentage of the portfolio.

    Parameters
    ----------
    broker: Broker
    data_provider: DataProvider
    order_factory: OrderFactory
    fixed_percentage: float
        should be set once for all signals. It corresponds to the fraction of a portfolio that we
        are investing in every asset on single trade.
        For example: fixed_percentage = 0.2, means that we are investing 20% of portfolio to
        any signal that is long or short.
    tolerance_percentage: float
        used by OrderFactory
    """

    def __init__(self, broker: Broker, data_provider: DataProvider, order_factory: OrderFactory,
                 signals_register: SignalsRegister, fixed_percentage: float, tolerance_percentage: float = 0.0):

        super().__init__(broker, data_provider, order_factory, signals_register)

        self.fixed_percentage = fixed_percentage
        self.tolerance_percentage = tolerance_percentage

    def _generate_market_orders(self, signals: List[Signal], time_in_force: TimeInForce, frequency: Frequency = None) \
            -> List[Optional[Order]]:
        target_percentages = {
            self._get_specific_ticker(signal.ticker): signal.suggested_exposure.value * self.fixed_percentage
            for signal in signals
        }

        market_order_list = self._order_factory.target_percent_orders(
            target_percentages, MarketOrder(), time_in_force, self.tolerance_percentage, frequency)

        return market_order_list
