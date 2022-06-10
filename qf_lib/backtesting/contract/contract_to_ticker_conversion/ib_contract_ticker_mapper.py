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
from typing import Dict, Optional


from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.brokers.ib_broker.ib_contract import IBContract


class IBContractTickerMapper(ContractTickerMapper):
    """ IB IBContract mapper that can be used for live trading. Maps Tickers onto Interactive Brokers IBContract objects.

    Parameters
    ----------
    ticker_to_contract: Dict[Ticker, IBContract]
        mapping between Tickers (also FutureTickers) and parameters that should be used for these tickers, when
        transforming them into Contracts.
    data_provider: Optional[DataProvider]
        data_provider used to obtain the value of the last trade date for various tickers. The parameter is optional
        and it is necessary only in case if the mapping between FutureTickers and Contracts is required.
    """

    def __init__(self, ticker_to_contract: Dict[Ticker, IBContract], data_provider: Optional[DataProvider] = None):
        self._validate_ticker_to_contract_mapping(ticker_to_contract)

        self._ticker_to_contract_dict = ticker_to_contract
        self._mapped_tickers = list(self._ticker_to_contract_dict.keys())
        self._contract_to_ticker_dict = {item: key for key, item in ticker_to_contract.items()}

        self._data_provider = data_provider

    def _validate_ticker_to_contract_mapping(self, ticker_to_contract: Dict[Ticker, IBContract]):
        mapped_contracts = ticker_to_contract.values()
        assert len(mapped_contracts) == len(set(mapped_contracts)), "The same IBContract was assigned to multiple " \
                                                                    "different tickers in the ticker_to_contract " \
                                                                    "parameter. Please, make sure that each " \
                                                                    "contract matches only one ticker."

    def contract_to_ticker(self, contract: IBContract) -> Ticker:
        """ It always maps to the specific ticker. """
        # Create a new instance of the IBContract, with the last_trade_date parameter removed
        contract_without_last_trade_date = IBContract.from_ib_contract(contract)
        contract_without_last_trade_date.last_trade_date = None

        # Search for the contract in the ticker to contract dictionary, ignoring last_trade_date if necessary
        ticker = self._contract_to_ticker_dict.get(contract, None) or \
            self._contract_to_ticker_dict.get(contract_without_last_trade_date, None)

        # Get the specific ticker for the given last trade date
        if isinstance(ticker, FutureTicker):
            if self._data_provider is None:
                raise ValueError(f"In order to map contract {contract} onto a corresponding ticker, it is necessary "
                                 f"to set the data_provider to obtain the ticker for the given last trade date.")

            chain_tickers = self._data_provider.get_futures_chain_tickers(
                ticker, ExpirationDateField.LastTradeableDate)[ticker]
            chain_tickers = chain_tickers.index[chain_tickers == contract.last_trade_date]
            ticker = chain_tickers[0] if not chain_tickers.empty else None

        if ticker is None:
            raise ValueError(f"Could not map Interactive Brokers contract {contract} onto a Ticker object.")

        return ticker

    def ticker_to_contract(self, ticker: Ticker) -> IBContract:
        ticker = ticker.get_current_specific_ticker() if isinstance(ticker, FutureTicker) else ticker
        contract = self._ticker_to_contract_dict.get(ticker, None)

        if not contract and ticker.security_type == SecurityType.FUTURE:
            contract = self._create_futures_contract(ticker)

        return contract

    def _create_futures_contract(self, specific_ticker: Ticker):
        """ Creates an IBContract instance for a given specific future ticker. """
        future_ticker = self._get_matching_future_ticker(specific_ticker)
        mapped_contract = self._ticker_to_contract_dict.get(future_ticker, None)

        if not mapped_contract:
            raise ValueError(f"Could not map the ticker {specific_ticker} onto Interactive Brokers contract.")
        elif self._data_provider is None:
            raise ValueError(f"In order to map ticker {specific_ticker} onto a corresponding IBContract, it is "
                             f"necessary to set the data_provider to obtain the last trade date value.")

        chain_tickers = self._data_provider.get_futures_chain_tickers(
            future_ticker, ExpirationDateField.LastTradeableDate)[future_ticker]

        try:
            last_trade_date = chain_tickers.loc[specific_ticker].to_pydatetime()
            contract = IBContract.from_ib_contract(mapped_contract)
            contract.last_trade_date = last_trade_date
            return contract
        except KeyError:
            raise ValueError(f"Cannot map the future ticker {specific_ticker} as it doesn't have a corresponding "
                             f"last trade date returned by the DataProvider.") from None

    def _get_matching_future_ticker(self, specific_ticker: Ticker) -> Optional[FutureTicker]:
        """ For a given ticker returns a corresponding future ticker if any exists. """
        matching_tickers = [fut_ticker for fut_ticker in self._mapped_tickers if isinstance(fut_ticker, FutureTicker)
                            and fut_ticker.belongs_to_family(specific_ticker)]

        if len(matching_tickers) > 1:
            raise ValueError(f"Ticker {specific_ticker} belongs to more then one future family: {matching_tickers}.")
        return matching_tickers[0] if matching_tickers else None
