from typing import List

from numpy import sign

from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent
from qf_lib.common.tickers.tickers import Ticker


class Position(object):
    def __init__(self, ticker: Ticker) -> None:
        self.ticker = ticker
        """Ticker identifying the position"""

        self.is_closed = False
        """Determines if the positions has been closed"""

        self.transactions = []     # type: List[FillEvent]
        """List of all transactions for the asset"""

        self.number_of_shares = 0  # type: int
        """ Number of shares held currently in the portfolio. Positive value means this is a Long position
        Negative value corresponds to a Short position"""

        self.current_price = 0.0   # type: float
        """ Current price of the asset used for market value calculation. Includes the Bid-Ask spread"""

        self.direction = 0         # type: int
        """ Direction of the position: Long = 1, Short = -1, Not defined = 0"""

    @property
    def market_value(self) -> float:
        """ Estimated current market value of the position """
        return self.number_of_shares * self.current_price

    def transact_fill_event(self, fill_event: FillEvent) -> float:
        """
        Update the state of a position by using the fill event containing information about datetime, price,
        quantity and commission.

        Returns
        -------
        For BUY transaction: much we paid for the transaction including commission (it will be a positive number)
        For SELL transaction: much we received for selling shares including commission (it will be a negative number)
        """
        self._check_if_open()
        self._check_if_direction_does_not_change(fill_event)
        assert fill_event.ticker == self.ticker, "Ticker of fill event has to match the ticker of a position"
        assert fill_event.quantity != 0, "`fill_quantity` shouldn't be 0"
        assert fill_event.price > 0.0, "`fill_price` must be positive. For short sales use a negative quantity"

        if not self.transactions:   # the first transaction decides the direction of the position
            self.direction = sign(fill_event.quantity)

        self.transactions.append(fill_event)
        self.number_of_shares += fill_event.quantity

        if self.number_of_shares == 0:  # close the position if the number of shares drops to zero
            self.is_closed = True

        return self._calculate_cost_of_transaction(fill_event)

    def update_price(self, bid_price: float, ask_price: float):
        """
        Sets the current price of the security in a way that takes into account the bid-ask spread
        This is used for market valuation of the open position.
        This method should be called every time we have have a new price
        """
        self._check_if_open()

        if self.number_of_shares > 0:  # we are long -> use the lower (bid) price
            self.current_price = bid_price
        elif self.number_of_shares < 0:  # we are short -> use the higher (ask) price
            self.current_price = ask_price

    def cost_basis(self) -> float:
        """
        This value includes both BUY and SELL transactions and their respective prices.
        For the long position it tells us what should be the value at which we sell all currently held shares
        in order to break even. The value includes all incurred transaction costs.
        """
        if self.number_of_shares == 0:
            return 0.0

        result = 0.0
        for transaction in self.transactions:
            result += (transaction.price * transaction.quantity)
            result += transaction.commission
        return result

    def average_cost_per_share(self) -> float:
        """
        For the long position it tells us what was the average price paid to acquire one share of the position.
        For short positions it tells us what was the average value we received for one share of the position.
        The value includes all incurred transaction costs and distributes them equally over all shares
        It is always a positive number.
        """
        cost = 0.0
        shares = 0

        for transaction in self.transactions:
            # take into account only BUY transaction if the position is long
            # take into account only SELL transaction if the position is short
            if sign(transaction.quantity) == self.direction:
                cost += (transaction.price * transaction.quantity)
                cost += transaction.commission
                shares += transaction.quantity
        if shares == 0:
            return 0
        return cost / shares

    def unrealised_pnl(self):
        """
        Calculate the unrealised pln of the position based on the market value.
        """
        return self.market_value - self.cost_basis()

    def realized_pnl(self):
        """
        Calculate the realized pln of the position.
        """
        avg_cost_ps = self.average_cost_per_share()
        pnl = 0.0

        for transaction in self.transactions:
            # take into account only SELL transaction if the position is long
            # take into account only BUY transaction if the position is short
            if sign(transaction.quantity) != self.direction:
                # reverse the sing as the transaction is always going in opposite direction to the position
                quantity = -transaction.quantity
                pnl += (transaction.price - avg_cost_ps) * quantity - transaction.commission
        return pnl

    @staticmethod
    def _calculate_cost_of_transaction(fill_event: FillEvent):
        """
        Calculates how much we paid to buy assets or how much we received for selling assets (including commission)
        For the proceeds of the assets we sold it returns a negative number
        """
        result = fill_event.price * fill_event.quantity
        result += fill_event.commission
        return result

    def _check_if_open(self):
        assert not self.is_closed, "The position has already been closed"

    def _check_if_direction_does_not_change(self, fill_event: FillEvent):
        """
        Checks if the position will be still of the same direction.
        We do not allow changing the direction from Long to Short and from Short to Long
        We should close the position first and then open a new one in the opposite direction.
        """
        sign_after_transaction = sign(self.number_of_shares + fill_event.quantity)
        change = abs(sign_after_transaction - self.direction)
        assert change < 2, "Transaction cannot change the direction of the position. " \
                           "Close the position and open new one in the opposite direction."
