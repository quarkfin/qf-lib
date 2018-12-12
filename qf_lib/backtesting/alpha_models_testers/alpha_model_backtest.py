from typing import List
import matplotlib.pyplot as plt

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession


class AlphaModelBacktest(object):
    """
    Performs a precise backtest of a selected alpha model
    """

    def __init__(self, ts: BacktestTradingSession, model: AlphaModel, tickers: List[Ticker], use_stop_losses=False):
        self._broker = ts.broker
        self._order_factory = ts.order_factory
        self._data_handler = ts.data_handler
        self._contract_ticker_mapper = ts.contract_ticker_mapper
        self._position_sizer = ts.position_sizer

        self._model = model
        self._tickers = list(set(tickers))  # remove potential duplicates
        self._use_stop_losses = use_stop_losses

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self._calculate_signals_and_place_orders()

    def _calculate_signals_and_place_orders(self):
        contracts = [self._contract_ticker_mapper.ticker_to_contract(ticker) for ticker in self._tickers]
        current_exposures = self._get_current_exposures(contracts)
        signals = []

        for ticker, contract in zip(self._tickers, contracts):
            signal = self._model.get_signal(ticker, current_exposures[contract])
            signals.append(signal)

        orders = self._position_sizer.size_signals(signals)

        self._broker.cancel_all_open_orders()

        market_orders = [order for order in orders if isinstance(order.execution_style, MarketOrder)]
        self._broker.place_orders(market_orders)

        if self._use_stop_losses:
            stop_orders = [order for order in orders if isinstance(order.execution_style, StopOrder)]
            self._broker.place_orders(stop_orders)

    def _get_current_exposures(self, contracts):
        current_exposures = {}
        positions = self._broker.get_positions()
        for contract in contracts:
            direction = next((position.direction for position in positions if position.contract() == contract), 0)
            current_exposures[contract] = Exposure(direction)
        return current_exposures
