from copy import deepcopy
from datetime import datetime
from typing import Optional, List, Dict

from numpy import sign

from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent
from qf_lib.backtesting.qstrader.portfolio.position import Position
from qf_lib.backtesting.qstrader.portfolio.trade import Trade
from qf_lib.backtesting.qstrader.data_handler.data_handler import DataHandler
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.prices_series import PricesSeries


class Portfolio(object):
    def __init__(self, data_handler: DataHandler, initial_cash: float, timer: Timer):
        """
        On creation, the Portfolio object contains no positions and all values are "reset" to the initial
        cash, with no PnL.
        """
        self.initial_cash = initial_cash
        self.data_handler = data_handler
        self.timer = timer

        self.current_portfolio_value = initial_cash
        self.current_cash = initial_cash

        # dates and portfolio values are keep separately because it is inefficient to append to the QFSeries
        # use get_portfolio_timeseries() to get them as a series.
        self.dates = []                 # type: List[datetime]
        self.portfolio_values = []      # type: List[float]

        self.open_positions_dict = {}   # type: Dict[Ticker, Position]
        self.closed_positions = []      # type: List[Position]
        self.trades = []                # type: List[Trade]

    def transact_fill_event(self, fill_event: FillEvent):
        """
        Adjusts positions to account for a transaction.
        Handles any new position or modification to a current position
        """

        position = self._get_or_create_position(fill_event.ticker)
        transaction_cost = position.transact_fill_event(fill_event)
        self.current_cash -= transaction_cost

        self._record_trade(position, fill_event)

        # if the position was closed: remove it from open positions and place in closed positions
        if position.is_closed:
            self.open_positions_dict.pop(fill_event.ticker)
            self.closed_positions.append(position)

    def update(self):
        """
        Updates the value of all positions that are currently open by getting the most recent price.
        """
        self.current_portfolio_value = self.current_cash

        all_tickers_in_portfolio = list(self.open_positions_dict.keys())
        # obtain the current market prices for all positions in one request
        current_prices_series = self.data_handler.get_last_available_price(tickers=all_tickers_in_portfolio)

        for ticker, position in self.open_positions_dict.items():
            security_price = current_prices_series[ticker]
            position.update_price(bid_price=security_price, ask_price=security_price)  # TODO: Model with Bid/Ask
            self.current_portfolio_value += position.market_value

        self.dates.append(self.timer.now())
        self.portfolio_values.append(self.current_portfolio_value)

    def get_position(self, ticker: Ticker) -> Optional[Position]:
        position = self.open_positions_dict.get(ticker, None)
        if position is None:
            return None

        return deepcopy(position)

    def get_portfolio_timeseries(self) -> PricesSeries:
        """
        Returns a timeseries of value of the portfolio expressed in currency units
        """
        portfolio_timeseries = PricesSeries(data=self.portfolio_values, index=self.dates)
        return portfolio_timeseries

    def _get_or_create_position(self, ticker: Ticker) -> Position:
        position = self.open_positions_dict.get(ticker, None)
        if position is None:
            position = Position(ticker)
            self.open_positions_dict[ticker] = position

        return position

    def _record_trade(self, position: Position, fill_event: FillEvent):
        """
        Trade is defined as a transaction that goes in the direction of making your position smaller.
        For example:
           selling part or entire long position is a trade
           buying back part or entire short position is a trade
           buying additional shares of existing long position is NOT a trade
        """
        is_a_trade = sign(fill_event.quantity) != sign(position.number_of_shares)
        if is_a_trade:
            time = fill_event.time
            ticker = position.ticker
            quantity = fill_event.quantity
            entry_price = position.average_cost_per_share()
            exit_price = fill_event.average_price_including_commission()
            trade = Trade(time=time,
                          ticker=ticker,
                          quantity=quantity,
                          entry_price=entry_price,
                          exit_price=exit_price)
            self.trades.append(trade)
