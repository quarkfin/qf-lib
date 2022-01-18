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

import re
from typing import Type

from pandas import to_datetime

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import PortaraTicker, Ticker
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries


class PortaraFutureTicker(FutureTicker, PortaraTicker):
    """Representation of a Future Ticker, designed to be used by the PortaraDataProvider.

    Parameters
    ----------
    name: str
        Field which contains a name (or a short description) of the FutureTicker, for example 'Cotton' or
        'Brent Crude Oil'. This does not need to be a ticker code.
    family_id: str
        Used to identify a given futures family. It should match the name of the file, which contains expiration dates
        for a chain of the futures contracts. For example, in case of Silver, the name of the file with
        expiration dates should be equal to 'SIA.txt' and the family_id should be equal to 'SIA{}'. The '{}' part of
        the family_id points to this part of the symbol, which should be filled with the month and year code in case
        of individual tickers. In case of Silver the following tickers will belong to the Futures family: SIA2021H,
        SIA2021K, SIA2021N, SIA2021U, SIA2021Z etc.
    N: int
        Since we chain individual tenors, we need to know which contract to select. N determines which contract is used
        at any given time when we have to select a specific contract (tenor). For example N parameter set to 1,
        denotes the first (front) future contract. N set to 2 will be the second contract and so on.
    days_before_exp_date: int
        Number of days before the expiration day of each of the contract, when the “current” specific contract
        should be substituted with the next consecutive one.
    point_value: int
        Used to define the size of the contract.
    designated_contracts: str
        It is a string, which represents all month codes, that are being downloaded and stored
        in the chain of future contracts. Any specific order of letters is not required. E.g. providing this
        parameter value equal to "HMUZ", would restrict the future chain to only the contracts, which expire in
        March, June, September and December, even if contracts for any other months exist and are returned by the
        DataProvider get_futures_chain_tickers function.
    """

    def __init__(self, name: str, family_id: str, N: int, days_before_exp_date: int, point_value: int = 1,
                 designated_contracts: str = "FGHJKMNQUVXZ", security_type: SecurityType = SecurityType.FUTURE):
        if not len(designated_contracts) > 0:
            raise ValueError("At least one month code should be provided.")

        super().__init__(name, family_id, N, days_before_exp_date, point_value, designated_contracts, security_type)

    def _get_futures_chain_tickers(self) -> QFSeries:
        futures_chain_tickers_df = self._data_provider.get_futures_chain_tickers(
            self, [ExpirationDateField.LastTradeableDate])[self]
        futures_chain_tickers_series = futures_chain_tickers_df.loc[:, ExpirationDateField.LastTradeableDate]

        # Filter out the non-designated contracts
        month_codes = "|".join(self.designated_contracts)
        contracts_pattern = self.family_id.format(f"\\d{{4}}({month_codes})")
        designated_contracts = futures_chain_tickers_series.index[
            futures_chain_tickers_series.index.map(lambda t: bool(re.search(f"^{contracts_pattern}$", t.as_string())))]
        futures_chain_tickers_series = futures_chain_tickers_series.loc[designated_contracts]

        futures_chain_tickers = QFSeries(futures_chain_tickers_series.index, futures_chain_tickers_series.values)
        futures_chain_tickers.index = to_datetime(futures_chain_tickers.index)

        return futures_chain_tickers

    def belongs_to_family(self, ticker: PortaraTicker) -> bool:
        """
        Function, which takes a specific PortaraTicker, and verifies if it belongs to the family of futures contracts,
        identified by the PortaraFutureTicker and returns true if that is the case (false otherwise).
        """
        pattern = self.family_id.format("\\d{4}[A-Z]")
        return bool(re.match(f"^{pattern}$", ticker.ticker)) and \
            (ticker.point_value, ticker.security_type) == (self.point_value, self.security_type)

    def supported_ticker_type(self) -> Type[Ticker]:
        return PortaraTicker
