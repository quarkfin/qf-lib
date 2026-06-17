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
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.data_providers.data_provider import DataProvider


class InitialRiskPositionSizer(PositionSizer):
    """
    Sizes positions from risk per trade and the signal's ``fraction_at_risk`` (typically ATR-based).

    For each signal:

    ``target_percentage = (initial_risk / fraction_at_risk) * suggested_exposure.value``

    Optionally capped by ``max_target_percentage``.

    Parameters
    ----------
    broker: Broker
    data_provider: DataProvider
    order_factory: OrderFactory
    signals_register: SignalsRegister
    initial_risk: float
        Maximum portfolio fraction you are willing to lose if the stop is hit on one trade.
        For example ``0.02`` means 2% of portfolio at risk per position.
    max_target_percentage: float, optional
        Upper cap on absolute target weight. ``None`` disables the cap.
    tolerance_percentage: float
        Passed to ``OrderFactory.target_percent_orders``.

    Examples
    --------
    ``size_signals`` sizes from ``initial_risk / fraction_at_risk`` (then applies exposure sign).
    With portfolio 100,000, price 100, ``initial_risk=0.05``, and ``fraction_at_risk=0.02``:

    >>> sizer = InitialRiskPositionSizer(
    ...     broker, data_provider, order_factory, BacktestSignalsRegister(), initial_risk=0.05)
    >>> signal = Signal(ticker, Exposure.LONG, fraction_at_risk=0.02, last_available_price=100.0, creation_time=now)
    >>> orders = sizer.size_signals([signal], use_stop_losses=False)
    >>> orders[0].quantity
    2500.0

    The same signal with ``max_target_percentage=1.0`` caps leverage at 100% of portfolio (1,000 shares):

    >>> capped_sizer = InitialRiskPositionSizer(
    ...     broker, data_provider, order_factory, BacktestSignalsRegister(),
    ...     initial_risk=0.05, max_target_percentage=1.0)
    >>> capped_sizer.size_signals([signal], use_stop_losses=False)[0].quantity
    1000.0
    """

    def __init__(self, broker: Broker, data_provider: DataProvider, order_factory: OrderFactory,
                 signals_register: SignalsRegister, initial_risk: float, max_target_percentage: float = None,
                 tolerance_percentage: float = 0.0):
        super().__init__(broker, data_provider, order_factory, signals_register)

        assert is_finite_number(initial_risk), "Initial risk has to be a finite number"
        assert initial_risk >= 0, "Initial risk has to be positive"

        self._initial_risk = initial_risk
        self.max_target_percentage = max_target_percentage
        self.tolerance_percentage = tolerance_percentage

    @property
    def initial_risk(self):
        return self._initial_risk

    def _generate_market_orders(self, signals: List[Signal], time_in_force: TimeInForce, frequency: Frequency = None) \
            -> List[Optional[Order]]:

        target_percentages = {
            self._get_specific_ticker(signal.ticker): self._compute_target_percentage(signal)
            for signal in signals
        }

        market_order_list = self._order_factory.target_percent_orders(
            target_percentages, MarketOrder(), time_in_force, self.tolerance_percentage, frequency
        )

        return market_order_list

    def _cap_max_target_percentage(self, initial_target_percentage: float):
        """
        Sometimes the target percentage can be excessive to be executed by the broker (might exceed margin requirement)
        Cap the target percentage to the max value defined in this function
        """
        if (self.max_target_percentage is not None) and (initial_target_percentage > self.max_target_percentage):
            self.logger.info("Target Percentage: {} above the maximum of {}. Setting the target percentage to {}"
                             .format(initial_target_percentage, self.max_target_percentage, self.max_target_percentage))
            return self.max_target_percentage
        return initial_target_percentage

    def _compute_target_percentage(self, signal):
        if not is_finite_number(signal.fraction_at_risk) or signal.fraction_at_risk == 0.0:
            self.logger.warn("Invalid Fraction at Risk = {} for {}. Setting target percentage = 0.0".format(
                signal.fraction_at_risk, signal.ticker))
            return 0.0
        target_percentage = self._initial_risk / signal.fraction_at_risk
        self.logger.info("Target Percentage for {}: {}".format(signal.ticker, target_percentage))

        target_percentage = self._cap_max_target_percentage(target_percentage)

        target_percentage *= signal.suggested_exposure.value  # preserve the direction (-1, 0 , 1)
        self.logger.info("Target Percentage considering direction for {}: {}".format(signal.ticker,
                                                                                     target_percentage))

        assert is_finite_number(target_percentage), "target_percentage has to be a finite number"
        return target_percentage
