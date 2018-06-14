from datetime import datetime
from typing import List, Dict

from numpy import sign

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order_fill import OrderFill
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.prices_series import PricesSeries


class Portfolio(object):
    def __init__(self, data_handler: DataHandler, initial_cash: float, timer: Timer,
                 contract_to_ticker_mapper: ContractTickerMapper):
        """
        On creation, the Portfolio object contains no positions and all values are "reset" to the initial
        cash, with no PnL.
        """
        self.initial_cash = initial_cash
        self.data_handler = data_handler
        self.timer = timer
        self.contract_to_ticker_mapper = contract_to_ticker_mapper

        self.current_portfolio_value = initial_cash
        self.current_cash = initial_cash

        # dates and portfolio values are keep separately because it is inefficient to append to the QFSeries
        # use get_portfolio_timeseries() to get them as a series.
        self.dates = []                 # type: List[datetime]
        self.portfolio_values = []      # type: List[float]

        self.open_positions_dict = {}   # type: Dict[Contract, BacktestPosition]
        self.closed_positions = []      # type: List[BacktestPosition]
        self.trades = []                # type: List[Trade]

    def transact_order_fill(self, order_fill: OrderFill):
        """
        Adjusts positions to account for a transaction.
        Handles any new position or modification to a current position
        """

        position = self._get_or_create_position(order_fill.contract)
        transaction_cost = position.transact_order_fill(order_fill)
        self.current_cash -= transaction_cost

        self._record_trade(position, order_fill)

        # if the position was closed: remove it from open positions and place in closed positions
        if position.is_closed:
            self.open_positions_dict.pop(order_fill.contract)
            self.closed_positions.append(position)

    def update(self):
        """
        Updates the value of all positions that are currently open by getting the most recent price.
        """
        self.current_portfolio_value = self.current_cash

        contracts = self.open_positions_dict.keys()
        contract_to_ticker_dict = {
            contract: self.contract_to_ticker_mapper.contract_to_ticker(contract) for contract in contracts
        }

        all_tickers_in_portfolio = list(contract_to_ticker_dict.values())
        current_prices_series = self.data_handler.get_last_available_price(tickers=all_tickers_in_portfolio)

        for contract, position in self.open_positions_dict.items():
            ticker = contract_to_ticker_dict[contract]
            security_price = current_prices_series[ticker]
            position.update_price(bid_price=security_price, ask_price=security_price)  # TODO: Model with Bid/Ask
            self.current_portfolio_value += position.market_value

        self.dates.append(self.timer.now())
        self.portfolio_values.append(self.current_portfolio_value)

    def get_portfolio_timeseries(self) -> PricesSeries:
        """
        Returns a timeseries of value of the portfolio expressed in currency units
        """
        portfolio_timeseries = PricesSeries(data=self.portfolio_values, index=self.dates)
        return portfolio_timeseries

    def _get_or_create_position(self, contract: Contract) -> BacktestPosition:
        position = self.open_positions_dict.get(contract, None)
        if position is None:
            position = BacktestPosition(contract)
            self.open_positions_dict[contract] = position

        return position

    def _record_trade(self, position: BacktestPosition, order_fill: OrderFill):
        """
        Trade is defined as a transaction that goes in the direction of making your position smaller.
        For example:
           selling part or entire long position is a trade
           buying back part or entire short position is a trade
           buying additional shares of existing long position is NOT a trade
        """
        is_a_trade = sign(order_fill.quantity) != sign(position.number_of_shares)
        if is_a_trade:
            time = order_fill.time
            contract = position._contract
            quantity = order_fill.quantity
            entry_price = position.avg_cost_per_share()
            exit_price = order_fill.average_price_including_commission()
            trade = Trade(time=time,
                          contract=contract,
                          quantity=quantity,
                          entry_price=entry_price,
                          exit_price=exit_price)
            self.trades.append(trade)
