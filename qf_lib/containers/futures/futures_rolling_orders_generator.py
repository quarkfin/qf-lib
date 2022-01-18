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
from typing import Sequence, List, Set

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker


class FuturesRollingOrdersGenerator:
    """ Class responsible for generating close orders for expired future contracts. The close order is generated after
    the expiration date is reached (which is the original future ticker expiration date - days before exp date).
    If there still exists a position open for a contract even though the original future ticker expiration date is
    reached, an additional warning is generated.

    Parameters
    ----------
    future_tickers: Sequence[FutureTicker]
        Future tickers for which the contract rolling should be performed
    timer: Timer
        Timer used to verify, whether the final expiration dates of any contract have not been reached
    broker: Broker
        Broker used to get the list of currently open positions in the portfolio
    order_factory: OrderFactory
        Order Factory used to create orders to close the expired contracts
    """

    def __init__(self, future_tickers: Sequence[FutureTicker], timer: Timer, broker: Broker,
                 order_factory: OrderFactory):
        self._future_tickers = future_tickers
        self._timer = timer
        self._broker = broker
        self._order_factory = order_factory

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def generate_close_orders(self) -> List[Order]:
        """
        Close contracts for which a new futures contract from the same futures family should be open.
        """
        if not self._future_tickers:
            return []

        # Get all futures contracts, for which there exist an open position in the portfolio
        open_positions = self._broker.get_positions()

        # Get current specific tickers
        def valid_ticker(fut_ticker: FutureTicker) -> Ticker:
            try:
                return fut_ticker.get_current_specific_ticker()
            except NoValidTickerException:
                pass

        # Indicates if the ticker should be checked for rolling (corresponding future ticker was passed on init) or not
        def should_be_rolled(spec_ticker: Ticker) -> bool:
            return any(fut_ticker.belongs_to_family(spec_ticker) for fut_ticker in self._future_tickers)

        valid_specific_tickers = {valid_ticker(fut_ticker) for fut_ticker in self._future_tickers}  # type: Set[str]

        # Get all the contracts, which should be rolled and which do not contain the most recent specific ticker
        expired_contracts = {
            position.ticker() for position in open_positions
            if should_be_rolled(position.ticker()) and position.ticker() not in valid_specific_tickers
        }

        if expired_contracts:
            # Create close market orders for each of the overlapping, old future contracts
            market_order_list = self._order_factory.target_percent_orders(
                {contract: 0 for contract in expired_contracts}, MarketOrder(), TimeInForce.GTC
            )
            self._generate_expiration_warnings(expired_contracts)

        else:
            market_order_list = []

        return market_order_list

    def _generate_expiration_warnings(self, expired_contracts: Set[Ticker]):
        """
        Checks if the ticker still can be found in the portfolio even though the real expiration date (non-shifted)
        already passed.
        """
        for expired_specific_ticker in expired_contracts:
            corresponding_future_tickers = [fut_ticker for fut_ticker in self._future_tickers
                                            if fut_ticker.belongs_to_family(expired_specific_ticker)]
            assert len(corresponding_future_tickers) == 1, "The ticker should belong to only one future family"
            future_ticker = corresponding_future_tickers[0]
            exp_dates = future_ticker.get_expiration_dates()
            date = exp_dates[exp_dates == expired_specific_ticker].index[0]
            if date <= self._timer.now():
                self.logger.error("{} - Contract {} still found in the portfolio after expiration date {}"
                                  .format(self._timer.now(), expired_specific_ticker, date))
