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
from typing import Union

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.containers.futures.future_ticker import BloombergFutureTicker


class DummyBloombergContractTickerMapper(ContractTickerMapper):
    """
    Dummy BloombergTicker-Contract mapper.
    """
    def __init__(self):
        self._contract_to_future_ticker = {}

    def contract_to_ticker(self, contract: Contract, strictly_to_specific_ticker=True) -> BloombergTicker:
        """
        The parameter strictly_to_specific_ticker allows to map a Future contract to either BloombergTicker (default) or
        BloombergFutureTicker. E.g. contract with security_type = "FUT" and symbol = "CTZ9 Comdty" can be either mapped
        to BloombergTicker("CTZ9 Comdty") or a BloombergFutureTicker, which corresponds to the "CT{} Comdty" futures
        family.
        """

        if contract.security_type == 'STK' or strictly_to_specific_ticker:
            return BloombergTicker(ticker=contract.symbol)
        elif contract.security_type == 'FUT':
            try:
                return self._contract_to_future_ticker[contract]
            except KeyError:
                raise ValueError("No futures tickers matching contract {}".format(contract))
        else:
            raise ValueError("Not able to derive ticker from {} security type".format(contract.security_type))

    def ticker_to_contract(self, ticker: Union[BloombergTicker, BloombergFutureTicker]) -> Contract:
        """
        The security type is derived according to the type of the Ticker - in case of BloombergTicker the 'STK' security
        type is chosen and in case of BloombergFutureTicker - the 'FUT' security type.
        """
        if isinstance(ticker, BloombergFutureTicker):
            contract = Contract(symbol=ticker.ticker, security_type='FUT', exchange='SIM_EXCHANGE',
                                contract_size=ticker.point_value)

            self._contract_to_future_ticker[contract] = ticker
            return contract
        elif isinstance(ticker, BloombergTicker):
            return Contract(symbol=ticker.ticker, security_type='STK', exchange='SIM_EXCHANGE')

        else:
            raise ValueError("Not able to derive security type for ticker {}".format(ticker.ticker))
