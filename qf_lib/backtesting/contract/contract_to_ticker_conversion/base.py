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
from typing import Any

from qf_lib.common.tickers.tickers import Ticker


class ContractTickerMapper(metaclass=ABCMeta):
    @abstractmethod
    def contract_to_ticker(self, contract: Any) -> Ticker:
        """ Maps Broker specific contract objects onto corresponding Tickers.

        Parameters
        ----------
        contract: Any
            broker specific object, which is used to identify an asset (e.g. Contracts for Interactive Brokers,
            Tickers for Bloomberg EMSX etc.)

        Returns
        -------
        Ticker
            corresponding ticker
        """
        pass

    @abstractmethod
    def ticker_to_contract(self, ticker: Ticker) -> Any:
        """Maps ticker to corresponding ticker.

        Parameters
        ----------
        ticker: Ticker
            ticker that should be mapped

        Returns
        -------
        Any
            corresponding broker specific object
        """
        pass

    def __str__(self):
        return self.__class__.__name__
