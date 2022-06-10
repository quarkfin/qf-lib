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

from qf_lib.backtesting.portfolio.position import Position
from qf_lib.common.tickers.tickers import Ticker


class BinancePosition(Position):
    def __init__(self, ticker: Ticker, quantity: float):
        self._ticker = ticker
        self._quantity = quantity

    def ticker(self) -> Ticker:
        return self._ticker

    def quantity(self) -> float:
        return self._quantity

    def __str__(self):
        return f'BinancePosition(ticker: {self._ticker}, quantity: {self._quantity})'
