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

""" Map Bloomberg Tickers onto IB Contracts. """
from demo_scripts.demo_configuration.demo_ioc import container

from qf_lib.backtesting.contract.contract_to_ticker_conversion.ib_contract_ticker_mapper import IBContractTickerMapper
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.brokers.ib_broker.ib_contract import IBContract


def map_future_ticker_to_contract():
    mapping = {
        BloombergFutureTicker('Copper', 'HG{} Comdty', 1, 1, 250): IBContract("HG", SecurityType.FUTURE, "NYMEX",
                                                                              "25000", "USD"),
        BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100): IBContract("PA", SecurityType.FUTURE, "NYMEX", "100",
                                                                              "", str_to_date("2020-03-27"))
    }
    data_provider = container.resolve(BloombergDataProvider)

    contract_ticker_mapper = IBContractTickerMapper(mapping, data_provider)
    current_time = str_to_date("2020-12-01")

    for future_ticker in mapping.keys():
        if isinstance(future_ticker, BloombergFutureTicker):
            future_ticker.initialize_data_provider(SettableTimer(current_time), data_provider)

    print("\nMapping PAH20 Comdty ticker to IB contract")
    ticker = BloombergTicker("PAH20 Comdty", SecurityType.FUTURE, 100)
    contract = contract_ticker_mapper.ticker_to_contract(ticker)
    print(f"Ticker mapped onto the following contract: {contract}")

    print("\nMapping IBContract onto ticker")
    contract = IBContract("PA", SecurityType.FUTURE, "NYMEX", "100", "", str_to_date("2020-03-27"))
    ticker = contract_ticker_mapper.contract_to_ticker(contract)
    print(f"Contract mapped onto the following ticker: {ticker}")

    print("\nMapping HGH20 Comdty ticker - Copper, March 2020 futures contracts")
    ticker = BloombergTicker("HGH20 Comdty", SecurityType.FUTURE, 250)
    contract = contract_ticker_mapper.ticker_to_contract(ticker)
    print(f"Ticker mapped onto the following contract: {contract}")

    print("\nMapping IBContract onto ticker")
    contract = IBContract("HG", SecurityType.FUTURE, "NYMEX", "25000", "USD", str_to_date("2021-01-27"))
    ticker = contract_ticker_mapper.contract_to_ticker(contract)
    print(f"Contract mapped onto the following ticker: {ticker}")


if __name__ == '__main__':
    map_future_ticker_to_contract()
