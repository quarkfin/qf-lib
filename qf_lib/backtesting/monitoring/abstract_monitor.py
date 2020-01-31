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

from qf_lib.backtesting.portfolio.transaction import Transaction


class AbstractMonitor(metaclass=ABCMeta):
    """
    AbstractMonitor is a class providing an interface for
    all inherited Monitor classes (live, historic, custom, etc).
    Monitor should be subclassed according to the use.
    """

    @abstractmethod
    def real_time_update(self, timestamp: datetime):
        """
        Update a basic statistics.
        This method should be light as it might be called after every transaction or price update
        """
        raise NotImplementedError("Should implement real_time_update()")

    @abstractmethod
    def end_of_day_update(self, timestamp: datetime):
        """
        Update the statistics after a whole day of trading. Should be used in live trading only
        """
        raise NotImplementedError("Should implement end_of_day_update()")

    @abstractmethod
    def end_of_trading_update(self, timestamp: datetime = None):
        """
        Final update at the end of backtest session
        """
        raise NotImplementedError("Should implement end_of_trading_update()")

    @abstractmethod
    def record_transaction(self, transaction: Transaction):
        """
        This method is called every time ExecutionHandler creates a new Transaction
        """
        raise NotImplementedError("Should implement record_transaction()")
