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
from typing import Union, Sequence

from qf_lib.backtesting.broker.backtest_broker import BacktestBroker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.event_manager import EventManager
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.orders_filter.orders_filter import OrdersFilter
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.helpers import compute_container_hash


class BacktestTradingSession(TradingSession):
    """
    Encapsulates the settings and components for carrying out a backtest session. Pulls for data every day.
    """

    def __init__(self, contract_ticker_mapper: ContractTickerMapper, start_date, end_date,
                 position_sizer: PositionSizer, orders_filters: Sequence[OrdersFilter], data_handler: DataHandler,
                 timer: SettableTimer, notifiers: Notifiers, portfolio: Portfolio, events_manager: EventManager,
                 monitor: BacktestMonitor, broker: BacktestBroker, order_factory: OrderFactory, frequency: Frequency,
                 backtest_result: BacktestResult):
        """
        Set up the backtest variables according to what has been passed in.
        The data_provider parameter of the BacktestTradingSession points to a Data Handler object.
        """
        super().__init__()
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.contract_ticker_mapper = contract_ticker_mapper
        self.start_date = start_date
        self.end_date = end_date

        self.notifiers = notifiers

        self.event_manager = events_manager
        self.data_handler = data_handler
        self.data_provider = data_handler  # type: DataHandler

        self.portfolio = portfolio
        self.position_sizer = position_sizer
        self.orders_filters = orders_filters
        self.monitor = monitor
        self.timer = timer
        self.order_factory = order_factory
        self.broker = broker
        self.frequency = frequency
        self.backtest_result = backtest_result

        self._hash_of_data_bundle = None

    def use_data_preloading(self, tickers: Union[Ticker, Sequence[Ticker]], time_delta: RelativeDelta = None):
        if time_delta is None:
            time_delta = RelativeDelta(years=1)
        data_start = self.start_date - time_delta

        # The tickers and price fields are sorted in order to always return the same hash of the data bundle for
        # the same set of tickers and fields
        tickers, _ = convert_to_list(tickers, Ticker)
        self.data_handler.use_data_bundle(sorted(tickers), sorted(PriceField.ohlcv()), data_start, self.end_date,
                                          self.frequency)
        self._hash_of_data_bundle = compute_container_hash(self.data_handler.data_provider.data_bundle)
        self.logger.info("Preloaded data hash value {}".format(self._hash_of_data_bundle))

    def get_preloaded_data_checksum(self) -> str:
        """
        Returns the checksum value computed as a hexadecimal digest on the preloaded data bundle.

        Returns
        -------
        str
            checksum of the preloaded data bundle
        """
        if self._hash_of_data_bundle is not None:
            return self._hash_of_data_bundle
        else:
            raise ValueError("Not able to compute checksum of data bundle. The data has not been preloaded yet.")

    def verify_preloaded_data(self, expected_checksum: str):
        """
        Verifies if the checksum computed on the preloaded data bundle is equal to the expected value. In case of
        differences ValueError is raised.

        Parameters
        -----------
        expected_checksum: str
            The expected checksum of the data bundle.
        """
        if self._hash_of_data_bundle is None:
            raise ValueError("Not able to compute checksum of data bundle. The data has not been preloaded yet.")
        elif self._hash_of_data_bundle != expected_checksum:
            raise ValueError("Data preloading was not successful. The expected checksum does not match the actual "
                             "value.")
