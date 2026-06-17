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
from typing import List, Optional

from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.common.enums.frequency import Frequency


class SimplePositionSizer(PositionSizer):
    """
    Converts each signal to a market order targeting a portfolio weight equal to ``Exposure`` value.

    ``Exposure.LONG`` (``1.0``) → invest **100%** of portfolio value in the asset.
    ``Exposure.SHORT`` (``-1.0``) → **-100%** (full short).
    ``Exposure.OUT`` (``0.0``) → flat.

    Default on
    :class:`~qf_lib.backtesting.trading_session.backtest_trading_session_builder.BacktestTradingSessionBuilder`.

    Examples
    --------

    >>> sizer = SimplePositionSizer(broker, data_provider, OrderFactory(broker, data_provider),
    ...                             BacktestSignalsRegister())
    >>> long_signal = Signal(ticker, Exposure.LONG, 0.02, 100.0, now)
    >>> orders = sizer.size_signals([long_signal], use_stop_losses=False)
    >>> orders[0].quantity
    1000.0

    >>> short_signal = Signal(ticker, Exposure.SHORT, 0.02, 100.0, now)
    >>> sizer.size_signals([short_signal], use_stop_losses=False)[0].quantity
    -1000.0
    """

    def _generate_market_orders(self, signals: List[Signal], time_in_force: TimeInForce, frequency: Frequency = None) \
            -> List[Optional[Order]]:
        target_percentages = {
            self._get_specific_ticker(signal.ticker): signal.suggested_exposure.value for signal in signals
        }
        market_order_list = self._order_factory.target_percent_orders(
            target_percentages, MarketOrder(), time_in_force, frequency=frequency
        )

        return market_order_list
