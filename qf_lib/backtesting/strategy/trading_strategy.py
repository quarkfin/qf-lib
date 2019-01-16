from typing import List

import numpy as np

from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class TradingStrategy(object):
    """
    Puts together models and all settings around it and generates orders on before market open
    """

    def __init__(self, ts: TradingSession, models: List[AlphaModel], tickers: List[Ticker],
                 use_stop_losses=False):

        self._broker = ts.broker
        self._order_factory = ts.order_factory
        self._data_handler = ts.data_handler
        self._contract_ticker_mapper = ts.contract_ticker_mapper
        self._position_sizer = ts.position_sizer

        self._models = models
        self._tickers = list(set(tickers))  # remove potential duplicates
        self._use_stop_losses = use_stop_losses
        self.logger = qf_logger.getChild(self.__class__.__name__)

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent=None):
        self.logger.info("on_before_market_open - Signal Generation Started")
        self._calculate_signals_and_place_orders()
        self.logger.info("on_before_market_open - Signal Generation Finished")

    def _calculate_signals_and_place_orders(self):
        contracts = [self._contract_ticker_mapper.ticker_to_contract(ticker) for ticker in self._tickers]
        current_exposures = self._get_current_exposures(contracts)
        signals = []

        for ticker, contract in zip(self._tickers, contracts):
            current_exposure = current_exposures[contract]
            self.logger.info("Current_Exposure: {}, {}, {}".format(current_exposure, contract, ticker))

            for model in self._models:
                signal = model.get_signal(ticker, current_exposure)
                signals.append(signal)
                self.logger.info(signal)

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

    def _get_current_exposures(self, contracts):
        current_exposures = {}
        positions = self._broker.get_positions()
        for contract in contracts:
            quantity = next((position.quantity() for position in positions if position.contract() == contract), 0)
            direction = np.sign(quantity)
            current_exposures[contract] = Exposure(direction)
        return current_exposures