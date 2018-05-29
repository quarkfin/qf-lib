import abc
from datetime import datetime

from qf_lib.backtesting.qstrader.events.event_base import Event
from qf_lib.common.tickers.tickers import Ticker


class PriceEvent(Event, metaclass=abc.ABCMeta):
    """
    Abstract class representing all events concerning new data about prices of assets.
    """
    def __init__(self, time: datetime, ticker: Ticker):
        super().__init__(time)
        self.ticker = ticker
