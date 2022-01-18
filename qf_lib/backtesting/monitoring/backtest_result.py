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

from datetime import datetime
from typing import List

from qf_lib.backtesting.signals.signals_register import SignalsRegister
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction


class BacktestResult:
    """
    BacktestResult is a class providing simple data model containing information about the backtest:
    for example it contains a portfolio with its timeseries and trades. It can also gather additional information
    """

    def __init__(self, portfolio: Portfolio, signals_register: SignalsRegister, backtest_name: str = None,
                 start_date: datetime = None, end_date: datetime = None, initial_risk: float = None):
        self.portfolio = portfolio
        self.signals_register = signals_register
        self.backtest_name = backtest_name
        self.start_date = start_date
        self.end_date = end_date
        self.initial_risk = initial_risk
        self.transactions = []  # type: List[Transaction]
