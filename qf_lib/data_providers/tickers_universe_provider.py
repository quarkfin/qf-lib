#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

from qf_lib.common.tickers.tickers import Ticker


class TickersUniverseProvider(object, metaclass=ABCMeta):
    """
    An interface for providers of tickers' universe data - list of Tickers included
    in the index at a specified date.
    """

    @abstractmethod
    def get_tickers_universe(self, universe_ticker: Ticker, date: datetime) -> List[Ticker]:
        """
        Parameters
        ----------
        universe_ticker
            ticker that describes a specific universe, which members will be returned
        date
            date for which current universe members' tickers will be returned
        """
        pass

    @abstractmethod
    def get_unique_tickers(self, universe_ticker: Ticker) -> List[Ticker]:
        """
        Returns the unique list of Tickers belonging to a specified universe regardless of the date.

        Parameters
        ----------
        universe_ticker
            ticker that describes a specific universe, which members will be returned

        Returns
        -------
        List[Ticker]
            list of Tickers belonging to the universe
        """
        pass
