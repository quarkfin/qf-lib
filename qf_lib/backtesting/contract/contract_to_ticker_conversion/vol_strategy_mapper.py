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

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker, BloombergTicker


class VolStrategyContractTickerMapper(ContractTickerMapper):
    """
    Contract Ticker Mapper that works only for one ticker - SVXY
    """

    symbol = "SVXY"
    bbg_suffix = "US Equity"
    sec_type = "STK"
    bbg_ticker_str = "{} {}".format(symbol, bbg_suffix)

    def contract_to_ticker(self, contract: Contract) -> Ticker:
        assert contract.symbol == self.symbol
        assert contract.security_type == self.sec_type
        return BloombergTicker(self.bbg_ticker_str)

    def ticker_to_contract(self, ticker: BloombergTicker) -> Contract:
        assert ticker.ticker == self.bbg_ticker_str
        return Contract(symbol=self.symbol, security_type=self.sec_type, exchange="ARCA")
