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
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer


class SimplePositionSizer(PositionSizer):
    """
    This SimplePositionSizer converts signals to orders which are the size of 100% of the current portfolio value
    """

    def _generate_market_order(self, contract, signal: Signal):
        target_percentage = signal.suggested_exposure.value
        market_order_list = self._order_factory.target_percent_orders(
            {contract: target_percentage}, MarketOrder(), TimeInForce.OPG)

        if len(market_order_list) == 0:
            return None

        assert len(market_order_list) == 1, "Only one order should be generated"
        return market_order_list[0]
