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
from collections import defaultdict
from typing import List, Dict, Sequence, Optional

import numpy as np

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.events.time_event.regular_time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


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
        self._broker = ts.broker
        self._order_factory = ts.order_factory
        self._data_handler = ts.data_handler
        self._contract_ticker_mapper = ts.contract_ticker_mapper
        self._position_sizer = ts.position_sizer
        self._timer = ts.timer

        self._model_tickers_dict = model_tickers_dict
        self._use_stop_losses = use_stop_losses
        self._signals = defaultdict(list)  # signals with date and "Ticker@AlphaModel" string
        self._signals_dates = []
        self._max_open_positions = max_open_positions

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self._log_configuration()

    def on_before_market_open(self, _: BeforeMarketOpenEvent = None):
        if self._timer.now().weekday() not in (5, 6):  # Skip saturdays and sundays
            self.logger.info("on_before_market_open - Signals Generation Started")
            signals = self._calculate_signals()
            self.logger.info("on_before_market_open - Signals Generation Finished")

            if self._max_open_positions is not None:
                self._adjust_number_of_open_positions(signals)

            self._save_signals(signals)

            self.logger.info("on_before_market_open - Placing Orders")
            self._place_orders(signals)
            self.logger.info("on_before_market_open - Orders Placed")

    def _adjust_number_of_open_positions(self, signals: List[Signal]):
        """
        Adjust the number of positions that, after placing the orders, will be open in th portfolio, so that it
        will not exceed the maximum number.

        In case if we already reached the maximum number of positions in the portfolio and we get 2 new signals,
        one for opening and one for closing a position, we ignore the opening position signal in case if during
        position closing an error would occur and the position will remain in the portfolio.

        While checking the number of all possible open positions we consider tickers and not contracts. Therefore
        (in case of e.g. a future contract) even if on a rolling day there would exist 2 contracts corresponding to one
        ticker, they would be counted as 1 open position.
        """

        def to_ticker(contract: Contract):
            # Map contract to corresponding ticker, where two contracts from one future family should be mapped into
            # the same one
            return self._contract_ticker_mapper.contract_to_ticker(contract, strictly_to_specific_ticker=False)

        open_positions = self._broker.get_positions()
        open_positions_tickers = set(to_ticker(position.contract()) for position in open_positions)

        # Signals, which correspond to either already open positions in the portfolio or indicate that a new position
        # should be open for the given contract (with Exposure = LONG or SHORT)
        position_opening_signals = [signal for signal in signals if signal.suggested_exposure != Exposure.OUT]

        # Check if the number of currently open positions in portfolio + new positions, that should be open according
        # to the signals, does not exceed the limit
        all_open_positions_tickers = open_positions_tickers.union(
            [signal.ticker for signal in position_opening_signals]
        )
        if len(all_open_positions_tickers) <= self._max_open_positions:
            return signals

        self.logger.info("The number of positions to be open exceeds the maximum limit of {}. Some of the signals need "
                         "to be changed.".format(self._max_open_positions))

        # Signals, which indicate openings of new positions in the portfolio
        new_positions_signals = [signal for signal in signals if signal.ticker not in open_positions_tickers and
                                 signal in position_opening_signals]

        # Compute how many signals need to be changed (their exposure has to be changed to OUT in order to fulfill the
        # requirements)
        number_of_signals_to_change = len(new_positions_signals) - (self._max_open_positions - len(open_positions_tickers))
        assert number_of_signals_to_change >= 0

        # Select a random subset of signals, for which the exposure will be set to OUT (in order not to exceed the
        # maximum), which would be deterministic across multiple backtests for the same period of time (certain seed)
        random.seed(self._timer.now())
        new_positions_signals = sorted(new_positions_signals, key=lambda s: s.fraction_at_risk)  # type: List[Signal]
        signals_to_change = random.sample(new_positions_signals, number_of_signals_to_change)

        for signal in signals_to_change:
            signal.suggested_exposure = Exposure.OUT

        return signals

    def _calculate_signals(self):
        current_positions = self._broker.get_positions()
        signals = []

        for model, tickers in self._model_tickers_dict.items():
            tickers = list(set(tickers))  # remove duplicates

            def map_valid_tickers(ticker):
                try:
                    return self._contract_ticker_mapper.ticker_to_contract(ticker)
                except NoValidTickerException:
                    return None

            contracts = [map_valid_tickers(ticker) for ticker in tickers]
            tickers_and_contracts = zip(tickers, contracts)
            valid_tickers_and_contracts = [(t, c) for t, c in tickers_and_contracts if c is not None]

            for ticker, contract in valid_tickers_and_contracts:
                current_exposure = self._get_current_exposure(contract, current_positions)
                signal = model.get_signal(ticker, current_exposure)
                signals.append(signal)

        return signals

    def _place_orders(self, signals):
        self.logger.info("Converting Signals to Orders using: {}".format(self._position_sizer.__class__.__name__))
        orders = self._position_sizer.size_signals(signals, self._use_stop_losses)

        self.logger.info("Cancelling all open orders")
        self._broker.cancel_all_open_orders()

        self.logger.info("Placing orders")
        self._broker.place_orders(orders)

    def _save_signals(self, signals: List[Signal]):
        tickers_to_models = {
            ticker: model.__class__.__name__ for model, tickers_list in self._model_tickers_dict.items()
            for ticker in tickers_list
        }

        tickers_to_signals = {
            ticker: None for model_tickers in self._model_tickers_dict.values() for ticker in model_tickers
        }

        tickers_to_signals.update({
            signal.ticker: signal for signal in signals
        })

        for ticker in tickers_to_signals.keys():
            signal = tickers_to_signals[ticker]
            model_name = tickers_to_models[ticker]

            self.logger.info(signal)

            ticker_str = ticker.as_string() + "@" + model_name
            self._signals[ticker_str].append((self._timer.now().date(), signal))

        self._signals_dates.append(self._timer.now())

    def get_signals(self):
        """
        Returns a QFDataFrame with all generated signals. The columns names are of the form TickerName@ModelName,
        and the rows are indexed by the time of signals generation.

        Returns
        --------
        QFDataFrame
            QFDataFrame with all generated signals
        """
        return QFDataFrame(data=self._signals, index=self._signals_dates)

    def _get_current_exposure(self, contract: Contract, current_positions: List[Position]) -> Exposure:
        matching_position_quantities = [position.quantity()
                                        for position in current_positions if position.contract() == contract]

        assert len(matching_position_quantities) in [0, 1]
        quantity = next(iter(matching_position_quantities), 0)
        current_exposure = Exposure(np.sign(quantity))
        return current_exposure

    def _log_configuration(self):
        self.logger.info("AlphaModelStrategy configuration:")
        for model, tickers in self._model_tickers_dict.items():
            self.logger.info('Model: {}'.format(str(model)))
            for ticker in tickers:
                try:
                    self.logger.info('\t Ticker: {}'.format(ticker.as_string()))
                except NoValidTickerException:
                    raise ValueError("Futures Tickers are not supported by the AlphaModelStrategy. Use the "
                                     "FuturesAlphaModelStrategy instead.")
