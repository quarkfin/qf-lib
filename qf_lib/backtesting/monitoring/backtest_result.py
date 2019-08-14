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

from qf_lib.backtesting.portfolio.portfolio import Portfolio


class BacktestResult(object):
    """
    BacktestResult is a class providing simple data model containing information about the backtest:
    for example it contains a portfolio with its timeseries and trades. It can also gather additional information
    """

    def __init__(self, portfolio: Portfolio, backtest_name: str = None,
                 start_date: datetime = None, end_date: datetime = None):
        self.portfolio = portfolio
        self.backtest_name = backtest_name
        self.start_date = start_date
        self.end_date = end_date
