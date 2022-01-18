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
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker


class SimulatedContractTickerMapper(ContractTickerMapper):
    """ Simulated contract to ticker mapper, which should be used for backtesting purposes. It is a simplified mapper,
    where both Broker and DataProvider use exactly the same data objects. """

    def contract_to_ticker(self, contract: Ticker) -> Ticker:
        """ Maps Contract objects into Tickers. """
        ticker = contract
        return ticker

    def ticker_to_contract(self, ticker: Ticker) -> Ticker:
        """ Maps contract parameters to corresponding ticker. """
        contract = ticker.get_current_specific_ticker() if isinstance(ticker, FutureTicker) else ticker
        return contract
