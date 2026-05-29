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
from typing import List, Optional, Dict
import numpy as np

from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.signals.signals_register import SignalsRegister
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.data_provider import DataProvider


class InitialRiskWithVolumePositionSizer(InitialRiskPositionSizer):
    """
    Extends :class:`InitialRiskPositionSizer` with a liquidity cap based on recent volume.

    After computing the initial-risk target value, order size is limited so that implied
    quantity does not exceed ``max_volume_percentage * mean(daily volume)`` over the last 100 days.
    Uses ``OrderFactory.target_value_orders`` instead of ``target_percent_orders``.

    Parameters
    ----------
    broker: Broker
    data_provider: DataProvider
    order_factory: OrderFactory
    signals_register: SignalsRegister
    initial_risk: float
        Maximum portfolio fraction at risk per trade (same as ``InitialRiskPositionSizer``).
    max_target_percentage: float, optional
        Upper cap on absolute target weight before the volume check.
    tolerance_percentage: float
        Passed to ``OrderFactory.target_value_orders``.
    max_volume_percentage: float
        Multiplier on mean daily volume (default ``1.0``). Lower values produce smaller positions
        in illiquid names.

    Examples
    --------
    Without a volume cap, ``initial_risk=0.05`` and ``fraction_at_risk=0.02`` would target 2,500 shares
    (same as :class:`InitialRiskPositionSizer`). With ``max_volume_percentage=0.1`` and mean daily
    volume 1,000, ``size_signals`` caps the market order at 100 shares:

    >>> sizer = InitialRiskWithVolumePositionSizer(
    ...         broker, data_provider, order_factory, BacktestSignalsRegister(),
    ...         initial_risk=0.05, max_volume_percentage=0.1)
    >>> signal = Signal(ticker, Exposure.LONG, fraction_at_risk=0.02,
    ...                     last_available_price=100.0, creation_time=now)
    >>> orders = sizer.size_signals([signal], use_stop_losses=False)
    >>> orders[0].quantity
    100.0

    In case the volume of the given day was 5,000, the cap will be set to 500 shares (10% of mean volume):

    >>> orders = sizer.size_signals([signal], use_stop_losses=False)
    >>> orders[0].quantity
    500.0
    """

    def __init__(self, broker: Broker, data_provider: DataProvider, order_factory: OrderFactory,
                 signals_register: SignalsRegister, initial_risk: float, max_target_percentage: float = None,
                 tolerance_percentage: float = 0.0, max_volume_percentage: float = 1.0):

        super().__init__(broker, data_provider, order_factory, signals_register, initial_risk, max_target_percentage,
                         tolerance_percentage)

        self._cached_futures_chains_dict: Dict[FutureTicker, FuturesChain] = dict()
        self._max_volume_percentage = max_volume_percentage

    def _generate_market_orders(self, signals: List[Signal], time_in_force: TimeInForce, frequency: Frequency = None) \
            -> List[Optional[Order]]:
        target_values = {
            self._get_specific_ticker(signal.ticker): self._compute_target_value(signal) for signal in signals
        }

        market_order_list = self._order_factory.target_value_orders(
            target_values, MarketOrder(), time_in_force, self.tolerance_percentage, frequency
        )

        return market_order_list

    def _compute_target_value(self, signal: Signal, frequency=Frequency.DAILY) -> float:
        """
        Caps the target value, so that according to historical volume data, the position will not exceed
        max_volume_percentage * mean volume within last 100 days.
        """
        ticker: Ticker = signal.ticker

        portfolio_value = self._broker.get_portfolio_value(ticker.currency)
        target_percentage = self._compute_target_percentage(signal)
        target_value = portfolio_value * target_percentage

        end_date = signal.creation_time
        start_date = end_date - RelativeDelta(days=100)

        if isinstance(ticker, FutureTicker):
            # Check if a futures chain instance already exists for this ticker and create it if not
            # The default adjustment method will be taken (FuturesAdjustmentMethod.NTH_NEAREST) as the volume should
            # not be adjusted
            if ticker not in self._cached_futures_chains_dict.keys():
                self._cached_futures_chains_dict[ticker] = FuturesChain(ticker, self._data_provider)

            volume_series: PricesSeries = self._cached_futures_chains_dict[ticker].get_price(PriceField.Volume,
                                                                                             start_date, end_date,
                                                                                             frequency)
        else:
            volume_series: PricesSeries = self._data_provider.get_price(ticker, PriceField.Volume, start_date, end_date,
                                                                        frequency)

        mean_volume = volume_series.mean()
        current_price = signal.last_available_price
        contract_size = ticker.point_value if isinstance(ticker, FutureTicker) else 1
        divisor = current_price * contract_size

        quantity = target_value / divisor

        if ticker.security_type != SecurityType.CRYPTO:
            quantity = float(np.floor(quantity))

        if abs(quantity) > mean_volume * self._max_volume_percentage:
            if ticker.security_type == SecurityType.CRYPTO:
                target_quantity = mean_volume * self._max_volume_percentage
            else:
                target_quantity = float(np.floor(mean_volume * self._max_volume_percentage))
            target_value = target_quantity * divisor * np.sign(quantity)
            self.logger.info(
                "InitialRiskWithVolumePositionSizer: capping {}.\n"
                "Initial quantity: {}\n"
                "Reduced quantity: {}".format(ticker.ticker, quantity, target_quantity))

        assert is_finite_number(target_value), "target_value has to be a finite number"
        return target_value
