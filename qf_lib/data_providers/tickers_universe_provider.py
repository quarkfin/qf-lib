from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List, Union

from qf_lib.common.tickers.tickers import Ticker


class TickersUniverseProvider(object, metaclass=ABCMeta):
    """
    An interface for providers of tickers' universe data - list of Tickers included
    in an index at a specified date.
    """
    @abstractmethod
    def get_tickers_universe(self, universe_name: Union[Ticker, str], date: datetime) -> List[Ticker]:
        pass
