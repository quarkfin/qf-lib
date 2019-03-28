from typing import List, Dict, Sequence

import numpy as np

from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class TradingStrategy(object):
    """
    Puts together models and all settings around it and generates orders on before market open
    """

    def __init__(self, ts: TradingSession, model_tickers_dict: Dict[AlphaModel, Sequence[Ticker]], use_stop_losses=True):
        """
        Parameters
        ----------
        ts: trading session
        model_tickers_dict: dict mapping models to list of tickers that the model trades. (The tickers for which the
            model gives recommendations)
        use_stop_losses: flag to use stop losses or not. If False all stop orders are ignored
        """

        self._broker = ts.broker
        self._order_factory = ts.order_factory
        self._data_handler = ts.data_handler
        self._contract_ticker_mapper = ts.contract_ticker_mapper
        self._position_sizer = ts.position_sizer
        self._timer = ts.timer

        self._model_tickers_dict = model_tickers_dict
        self._use_stop_losses = use_stop_losses
        self.signals_df = QFDataFrame()  # rows indexed by date and columns by "Ticker@AlphaModel" string

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self._log_configuration()

    def on_before_market_open(self, _: BeforeMarketOpenEvent=None):
        self.logger.info("on_before_market_open - Signals Generation Started")
        signals = self._calculate_signals()
        self.logger.info("on_before_market_open - Signals Generation Finished")

        self._save_signals(signals)

        self.logger.info("on_before_market_open - Placing Orders")
        self._place_orders(signals)
        self.logger.info("on_before_market_open - Orders Placed")

    def _calculate_signals(self):
        current_positions = self._broker.get_positions()
        signals = []

        for model, tickers in self._model_tickers_dict.items():
            tickers = list(set(tickers))  # remove duplicates
            contracts = [self._contract_ticker_mapper.ticker_to_contract(ticker) for ticker in tickers]

            for ticker, contract in zip(tickers, contracts):
                current_exposure = self._get_current_exposure(contract, current_positions)
                signal = model.get_signal(ticker, current_exposure)
                signals.append(signal)

        return signals

    def _place_orders(self, signals):
        self.logger.info("Converting Signals to Orders using: {}".format(self._position_sizer.__class__.__name__))
        orders = self._position_sizer.size_signals(signals)

        self.logger.info("Cancelling all open orders")
        self._broker.cancel_all_open_orders()

        market_orders = [order for order in orders if isinstance(order.execution_style, MarketOrder)]
        self.logger.info("Placing market orders")
        self._broker.place_orders(market_orders)

        if self._use_stop_losses:
            stop_orders = [order for order in orders if isinstance(order.execution_style, StopOrder)]
            self.logger.info("Placing stop orders")
            self._broker.place_orders(stop_orders)

    def _save_signals(self, signals: List[Signal]):
        for signal in signals:
            self.logger.info(signal)
            column = signal.ticker.as_string() + "@" + signal.alpha_model.__class__.__name__
            self.signals_df.loc[self._timer.now().date(), column] = signal  # save signals

    @staticmethod
    def _get_current_exposure(contract: Contract, current_positions: List[Position]) -> Exposure:
        matching_position_quantities = [position.quantity()
                                        for position in current_positions if position.contract() == contract]

        assert len(matching_position_quantities) in [0, 1]
        quantity = next(iter(matching_position_quantities), 0)
        current_exposure = Exposure(np.sign(quantity))
        return current_exposure

    def _log_configuration(self):
        self.logger.info("TradingStrategy configuration:")
        for model, tickers in self._model_tickers_dict.items():
            self.logger.info('Model: {}'.format(str(model)))
            for ticker in tickers:
                self.logger.info('\t Ticker: {}'.format(ticker.as_string()))
