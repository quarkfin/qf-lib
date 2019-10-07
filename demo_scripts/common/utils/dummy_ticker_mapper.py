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
from demo_scripts.common.utils.dummy_ticker import DummyTicker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker


class DummyTickerMapper(ContractTickerMapper):
    """
    Dummy ticker mapper designed for the demo purposes.
    """

    def contract_to_ticker(self, contract: Contract) -> Ticker:
        return DummyTicker(ticker=contract.symbol)

    def ticker_to_contract(self, ticker: Ticker) -> Contract:
        return Contract(symbol=ticker.ticker, security_type='STK', exchange='SIM_EXCHANGE')
