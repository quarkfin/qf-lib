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
from qf_lib.containers.series.qf_series import QFSeries


class TickersUniverseProvider(metaclass=ABCMeta):
    """
    An interface for data providers that supply the universe of tickers included in an index on a specified date.
    The class serves as a blueprint for implementing methods to retrieve tickers' data based on date criteria.
    """

    @abstractmethod
    def get_tickers_universe(self, universe_ticker: Ticker, date: datetime, **kwargs) -> List[Ticker]:
        """
        Retrieves the list of tickers included in the specified index at a given date.

        Parameters
        ----------
        universe_ticker: Ticker
            The ticker symbol representing the index or universe for which the tickers are being queried.
        date: datetime
            The date for which the tickers' universe data is requested.

        Returns
        -------
        List[Ticker]
            A list of tickers (Ticker objects) that were included in the index on the specified date.
        """
        pass

    @abstractmethod
    def get_unique_tickers(self, universe_ticker: Ticker) -> List[Ticker]:
        """
        Retrieves a list of unique tickers that belong to the specified universe, regardless of the date.

        Parameters
        ----------
        universe_ticker: Ticker
            The ticker symbol representing the index or universe for which the tickers are being queried.

        Returns
        -------
        List[Ticker]
            A list of unique tickers (Ticker objects) that are part of the specified universe (regardless of the date).
        """
        pass

    @abstractmethod
    def get_tickers_universe_with_weights(self, universe_ticker: Ticker, date: datetime, **kwargs) -> QFSeries:
        """
        Returns the tickers belonging to a specified universe, along with their corresponding weights, at a given date.
        The result is a QFSeries indexed by ticker objects, with the values representing the respective weights of
        each ticker in the universe.

        Parameters
        ----------
        universe_ticker: Ticker
            The ticker symbol representing the index or universe for which the tickers are being queried.
        date: datetime
            The date for which the tickers' universe data is requested.

        Returns
        -------
        QFSeries
            A QFSeries indexed by Ticker objects, where the values are the weights of the respective tickers
            in the universe at a given date.
        """
        pass
