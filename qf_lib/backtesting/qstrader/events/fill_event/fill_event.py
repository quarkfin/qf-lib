from datetime import datetime

from qf_lib.backtesting.qstrader.events.event_base import Event
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class FillEvent(Event):
    """
    Encapsulates the notion of a filled order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.

    TODO: Currently does not support filling positions at
    different prices. This will be simulated by averaging
    the cost.
    """

    def __init__(self, time: datetime, ticker: Ticker, quantity: int, price: float, commission: float) -> None:
        """
        Parameters
        ----------
        time
            time when the order was filled
        ticker
            ticker identifying the asset
        quantity
            filled quantity, positive for assets bought and negative for assets sold
        price
            price at which the trade was filled
        commission
            brokerage commission for carrying out the trade
        """
        super().__init__(time)
        self.ticker = ticker
        self.quantity = quantity
        self.price = price
        self.commission = commission

    def average_price_including_commission(self) -> float:
        """
        Returns average price that we obtain by selling asset or the average price that we paid to buy asset.
        It always includes the commission paid.
        """
        result = self.quantity * self.price
        result += self.commission
        result /= self.quantity
        return result

    def __str__(self):
        string_template = "{} - {:<25} -> Ticker: {:>17}, Quantity: {:>7}, Price: {:>7.2f}, Commission: {:>7.2f}".\
            format(date_to_str(self.time), self.__class__.__name__, self.ticker.as_string(),
                   self.quantity, self.price, self.commission
        )
        return string_template
