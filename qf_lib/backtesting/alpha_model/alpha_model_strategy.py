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
import random
from typing import List, Dict, Sequence, Optional, Union

import numpy as np

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_rolling_orders_generator import FuturesRollingOrdersGenerator


class AlphaModelStrategy(object):
    """
    Puts together models and all settings around it and generates orders on before market open.

    Parameters
    ----------
    ts: TradingSession
        Trading session
    model_tickers_dict: Dict[AlphaModel, Sequence[Ticker]]
        Dict mapping models to list of tickers that the model trades. (The tickers for which the
        model gives recommendations)
    use_stop_losses: bool
        flag indicating if the stop losses should be used or not. If False, all stop orders are ignored
    max_open_positions: None, int
        maximal number of positions that may be open at the same time in the portfolio. If the value is set to None,
        the number of maximal open positions is not limited.
    """

    def __init__(self, ts: TradingSession, model_tickers_dict: Dict[AlphaModel, Sequence[Ticker]], use_stop_losses=True,
                 max_open_positions: Optional[int] = None):

        all_future_tickers = [ticker for tickers_for_model in model_tickers_dict.values()
                              for ticker in tickers_for_model if isinstance(ticker, FutureTicker)]

        self._futures_rolling_orders_generator = self._get_futures_rolling_orders_generator(all_future_tickers,
                                                                                            ts.timer, ts.data_handler,
                                                                                            ts.broker, ts.order_factory,
                                                                                            ts.contract_ticker_mapper)
        self._broker = ts.broker
        self._order_factory = ts.order_factory
        self._data_handler = ts.data_handler
        self._contract_ticker_mapper = ts.contract_ticker_mapper
        self._position_sizer = ts.position_sizer
        self._orders_filters = ts.orders_filters
        self._timer = ts.timer

        self._model_tickers_dict = model_tickers_dict
        self._use_stop_losses = use_stop_losses
        self._max_open_positions = max_open_positions

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self._log_configuration()

    def _get_futures_rolling_orders_generator(self, future_tickers: Sequence[FutureTicker], timer: Timer,
                                              data_handler: DataHandler, broker: Broker, order_factory: OrderFactory,
                                              contract_ticker_mapper: ContractTickerMapper):

        # Initialize timer and data provider in case of FutureTickers
        for future_ticker in future_tickers:
            future_ticker.initialize_data_provider(timer, data_handler)

        return FuturesRollingOrdersGenerator(future_tickers, timer, broker, order_factory, contract_ticker_mapper)

    def on_before_market_open(self, _: BeforeMarketOpenEvent = None):
        if self._timer.now().weekday() not in (5, 6):  # Skip saturdays and sundays
            date = self._timer.now().date()
            self.logger.info("on_before_market_open [{}] Signals Generation Started".format(date))
            signals = self._calculate_signals()
            self.logger.info("on_before_market_open [{}] Signals Generation Finished".format(date))

            self.logger.debug("Signals: ")
            for s in signals:
                self.logger.debug(str(s))

            if self._max_open_positions is not None:
                self._adjust_number_of_open_positions(signals)

            self.logger.info("on_before_market_open [{}] Placing Orders".format(date))
            self._place_orders(signals)
            self.logger.info("on_before_market_open [{}] Orders Placed".format(date))

    def _adjust_number_of_open_positions(self, signals: List[Signal]):
        """
        Adjust the number of positions that, after placing the orders, will be open in th portfolio, so that it
        will not exceed the maximum number.

        In case if we already reached the maximum number of positions in the portfolio and we get 2 new signals,
        one for opening and one for closing a position, we ignore the opening position signal in case if during
        position closing an error would occur and the position will remain in the portfolio.

        Regarding Futures Contracts:
        While checking the number of all possible open positions we consider family of contracts
        (for example Gold) and not specific contracts (Jul 2020 Gold). Therefore even if 2 or more contracts
        corresponding to one family existed in the portfolio, they would be counted as 1 open position.
        """
        open_positions_specific_tickers = set(
            self._contract_ticker_mapper.contract_to_ticker(position.contract())
            for position in self._broker.get_positions()
        )

        def position_for_ticker_exists_in_portfolio(ticker: Ticker) -> bool:
            if isinstance(ticker, FutureTicker):
                # Check if any of specific tickers with open positions in portfolio belongs to tickers family
                return any([ticker.belongs_to_family(t) for t in open_positions_specific_tickers])
            else:
                return ticker in open_positions_specific_tickers

        # Signals corresponding to tickers, that already have a position open in the portfolio
        open_positions_signals = [signal for signal in signals if
                                  position_for_ticker_exists_in_portfolio(signal.ticker)]

        # Signals, which indicate openings of new positions in the portfolio
        new_positions_signals = [signal for signal in signals
                                 if not position_for_ticker_exists_in_portfolio(signal.ticker) and
                                 signal.suggested_exposure != Exposure.OUT]

        number_of_positions_to_be_open = len(new_positions_signals) + len(open_positions_signals)

        if number_of_positions_to_be_open > self._max_open_positions:
            self.logger.info("The number of positions to be open exceeds the maximum limit of {}. Some of the signals "
                             "need to be changed.".format(self._max_open_positions))

            no_of_signals_to_change = number_of_positions_to_be_open - self._max_open_positions

            # Select a random subset of signals, for which the exposure will be set to OUT (in order not to exceed the
            # maximum), which would be deterministic across multiple backtests
            random.seed(self._timer.now().timestamp())
            new_positions_signals = sorted(new_positions_signals, key=lambda s: s.fraction_at_risk)
            signals_to_change = random.sample(new_positions_signals, no_of_signals_to_change)

            for signal in signals_to_change:
                signal.suggested_exposure = Exposure.OUT

        return signals

    def _calculate_signals(self):
        current_positions = self._broker.get_positions()
        signals = []

        for model, tickers in self._model_tickers_dict.items():
            def get_specific_ticker(t: Ticker):
                try:
                    return t.ticker
                except NoValidTickerException:
                    return None

            currently_valid_tickers = [t for t in tickers if get_specific_ticker(t) is not None]
            for ticker in list(set(currently_valid_tickers)):  # remove duplicates
                current_exposure = self._get_current_exposure(ticker, current_positions)
                signal = model.get_signal(ticker, current_exposure)
                signals.append(signal)

        return signals

    def _place_orders(self, signals):
        self.logger.info("Converting Signals to Orders using: {}".format(self._position_sizer.__class__.__name__))
        orders = self._position_sizer.size_signals(signals, self._use_stop_losses)

        close_orders = self._futures_rolling_orders_generator.generate_close_orders()
        orders = orders + close_orders

        for orders_filter in self._orders_filters:
            if orders:
                self.logger.info("Filtering Orders based on selected requirements: {}".format(orders_filter))
                orders = orders_filter.adjust_orders(orders)

        self.logger.info("Cancelling all open orders")
        self._broker.cancel_all_open_orders()

        self.logger.info("Placing orders")
        self._broker.place_orders(orders)

    def _get_current_exposure(self, ticker: Union[Ticker, FutureTicker], current_positions: List[Position]) -> Exposure:
        """
        Returns current exposure of the given ticker in the portfolio. Alpha model strategy assumes there should be only
        one position per ticker in the portfolio. In case of future tickers this may not always be true - e.g. in case
        if a certain future contract expires and the rolling occurs we may end up with two positions open, when the
        old contract could not have been sold at the initially desired time. This situation usually does not happen
        often nor last too long, as the strategy will try to close the remaining position as soon as possible.
        Therefore, the current exposure of the ticker is defined as the exposure of the most recently opened position.
        """
        if isinstance(ticker, FutureTicker):
            matching_positions = [position for position in current_positions if
                                  ticker.belongs_to_family(
                                      self._contract_ticker_mapper.contract_to_ticker(position.contract()))
                                  ]
            assert len(matching_positions) in [0, 1, 2], "The number of open positions for a ticker should be 0, 1 or 2"
            all_specific_tickers = [self._contract_ticker_mapper.contract_to_ticker(position.contract())
                                    for position in matching_positions]
            assert len(set(all_specific_tickers)) == len(all_specific_tickers), "The number of open positions for a " \
                                                                                "specific ticker should be 0 or 1"
        else:
            matching_positions = [position for position in current_positions
                                  if position.contract() == self._contract_ticker_mapper.ticker_to_contract(ticker)]
            assert len(matching_positions) in [0, 1], "The number of open positions for a ticker should be 0 or 1"

        if len(matching_positions) > 0:
            newest_position = max(matching_positions, key=lambda pos: pos.start_time)
            quantity = newest_position.quantity()
            current_exposure = Exposure(np.sign(quantity))
        else:
            current_exposure = Exposure.OUT

        return current_exposure

    def _log_configuration(self):
        self.logger.info("AlphaModelStrategy configuration:")
        for model, tickers in self._model_tickers_dict.items():
            self.logger.info('Model: {}'.format(str(model)))
            for ticker in tickers:
                try:
                    self.logger.info('\t Ticker: {}'.format(ticker.name))
                except NoValidTickerException as e:
                    self.logger.info(e)
