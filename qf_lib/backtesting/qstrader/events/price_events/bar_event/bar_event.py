from datetime import datetime, timedelta

from qf_lib.backtesting.qstrader.events.price_events.price_event import PriceEvent
from qf_lib.common.tickers.tickers import Ticker


class BarEvent(PriceEvent):
    """
    Handles the event of receiving a new market
    open-high-low-close-volume bar, as would be generated
    via common data providers such as Yahoo Finance.
    """
    def __init__(self, ticker: Ticker, time: datetime, period: timedelta,
                 open_price: float, high_price: float, low_price: float, close_price: float, volume: float,
                 adj_close_price: float=None):
        """
        Initialises the BarEvent.

        Parameters
        ----------
        ticker
            ticker symbol, e.g. QuandlTicker('GOOG', 'WIKI')
        time
            date concerning a bar
        period
            period covered by the bar (e.g. one day, one month)
        open_price
            unadjusted opening price of the bar
        high_price
            unadjusted high price of the bar
        low_price
            unadjusted low price of the bar
        close_price
            unadjusted closed price of the bar
        volume
            volume of trading within the bar
        adj_close_price
            vendor adjusted closing price
        """
        super().__init__(time, ticker)
        self.period = period
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.adj_close_price = adj_close_price

    def __str__(self):
        format_str = "Type: %s, Ticker: %s, Time: %s, Period: %s, " \
            "Open: %s, High: %s, Low: %s, Close: %s, " \
            "Adj Close: %s, Volume: %s" % (
                         self.__class__.__name__, str(self.ticker), str(self.time),
                         str(self.period), str(self.open_price),
                         str(self.high_price), str(self.low_price),
                         str(self.close_price), str(self.adj_close_price),
                         str(self.volume)
            )
        return format_str

    def __repr__(self):
        return str(self)
