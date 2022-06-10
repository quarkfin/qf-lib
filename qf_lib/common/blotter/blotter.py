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

from qf_lib.backtesting.portfolio.transaction import Transaction


class Blotter(metaclass=ABCMeta):
    """
    Base Blotter class for all blotters
    Purpose of a blotter is to save all transactions.
    Most common implementation of blotters are with use of a CSV file, XLSX file or a database
    """

    @abstractmethod
    def save_transaction(self, transaction: Transaction):
        pass

    @abstractmethod
    def get_transactions(self, from_date: datetime = None, to_date: datetime = None) -> List[Transaction]:
        pass
