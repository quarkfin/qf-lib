from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

from qf_lib.common.tickers.tickers import Ticker


class TickersUniverseProvider(object, metaclass=ABCMeta):
    """
    An interface for providers of tickers' universe data - list of Tickers included
    in an index at a specified date.
    """

    @abstractmethod
    def get_tickers_universe(self, universe_ticker: Ticker, date: datetime) -> List[Ticker]:
        """
        Parameters
        ----------
        universe_ticker
            ticker that describes a specific universe, which members will be returned
        date
            date at which current universe members' tickers will be returned
        """
        pass
