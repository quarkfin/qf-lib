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

from typing import Any

from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker, BinanceTicker


class BinanceContractTickerMapper(ContractTickerMapper):

    def __init__(self, quote_ccy: str):
        self._quote_ccy = quote_ccy

    def contract_to_ticker(self, currency: str) -> Ticker:
        return BinanceTicker(currency, self._quote_ccy)

    def ticker_to_contract(self, ticker: Ticker) -> Any:
        return ticker.as_string()

    @property
    def quote_ccy(self):
        return self._quote_ccy
