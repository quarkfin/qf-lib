from datetime import datetime

from qf_lib.backtesting.contract.contract import Contract


class Trade(object):
    """
    Trade represents a pair of transactions that go in the opposite directions.
    For example:
        We buy 10 shares of X and then we sell 3 shares of X. This creates a trade when we buy and sell 3 shares of X
    """

    def __init__(self, time: datetime, contract: Contract, quantity: int, entry_price: float, exit_price: float,
                 risk_as_percent: float=float('nan')):
        self.time = time
        self.contract = contract
        self.quantity = quantity
        self.entry_price = entry_price
        self.exit_price = exit_price

        self.risk_as_percent = risk_as_percent

    def define_risk(self, risk_as_percent: float):
        self.risk_as_percent = risk_as_percent

    @property
    def pnl(self) -> float:
        """
        Profit or loss associated with a trade expressed in currency units
        including transaction costs and commissions
        """
        profit_loss = (self.exit_price - self.entry_price) * self.quantity
        return profit_loss

    @property
    def total_risk(self) -> float:
        """
        total risk associated with a trade expressed in currency units.
        It is the maximum loss that we expect to get while holding 'self.quantity' units of 'self.contract'
        """
        total_risk = abs(self.entry_price * self.risk_as_percent * self.quantity)
        return total_risk

    @property
    def r_multiply(self) -> float:
        """
        R multiply is the ratio of (profit or loss) to (total risk)
        """
        result = self.pnl / self.total_risk
        return result
