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

from abc import ABCMeta
from typing import Sequence

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.orders_filter.orders_filter import OrdersFilter
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.settings import Settings


class TradingSession(metaclass=ABCMeta):
    """
    Base class for all Trading Sessions. It configures all the elements of the trading environment.
    """

    def __init__(self):
        self.trading_session_name = None    # type: str
        self.settings = None                # type: Settings
        self.data_provider = None           # type: DataProvider

        self.timer = None                   # type: Timer
        self.monitor = None                 # type: AbstractMonitor
        self.broker = None                  # type: Broker

        self.contract_ticker_mapper = None  # type: ContractTickerMapper
        self.order_factory = None           # type: OrderFactory
        self.position_sizer = None          # type: PositionSizer
        self.orders_filters = None          # type: Sequence[OrdersFilter]
        self.event_manager = None           # type: EventManager

        self.notifiers = None               # type: Notifiers
        self.frequency = None               # type: Frequency

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def start_trading(self) -> None:
        """
        Carries out an while loop that processes incoming events. The loop continues until the EndTradingEvent occurs
        (e.g. no more data for the backtest).
        """
        self.logger.info("Trading Session - start trading...")
        while self.event_manager.continue_trading:
            self.event_manager.dispatch_next_event()

        self.logger.info("Trading Session - trading finished...")
        self.monitor.end_of_trading_update()

    @staticmethod
    def _create_event_manager(timer: Timer, notifiers: Notifiers):
        event_manager = EventManager(timer)

        event_manager.register_notifiers([
            notifiers.all_event_notifier,
            notifiers.empty_queue_event_notifier,
            notifiers.end_trading_event_notifier,
            notifiers.scheduler
        ])
        return event_manager
