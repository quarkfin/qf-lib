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
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries


class BloombergFutureTicker(FutureTicker, BloombergTicker):
    """Representation of a Future Ticker, designed to be used by the BloombergDataProvider.

    Parameters
    ----------
    name: str
        Field which contains a name (or a short description) of the FutureTicker.
    family_id: str
        Used to to verify if a specific BloombergTicker belongs to a certain futures family and to the active
        Ticker string, which can be further used by the data provider to download the chain of corresponding Tickers.
        The family ID pattern - e.g. for Cotton, an exemplary ticker string is of the following
        form: "CTZ9 Comdty". The "Z9" part denotes the month and year codes - this is the only variable part of the
        ticker. Thus, in order to verify if a ticker belongs to the cotton family, it should be in form of "CT{} Comdty".
        For all other ticker families, the family_id should be in the form of specific ticker with the month and
        year codes replaced with the "{}" placeholder.
    N: int
        Since we chain individual contracts, we need to know which one to select. N determines which contract is used
        at any given time when we have to select a specific contract. For example N parameter set to 1,
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
        BloombergDataProvider get_futures_chain_tickers function.
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

    def get_active_ticker(self) -> BloombergTicker:
        """ Returns the active ticker. """
        specific_ticker_string = self.family_id.format("A")
        return BloombergTicker.from_string(specific_ticker_string, self.security_type, self.point_value)

    def _get_futures_chain_tickers(self):
        """
        Function used to download the expiration dates of the futures contracts, in order to return afterwards current
        futures tickers. It uses the list of month codes of designated contracts and filter out these, that should not
        be considered by the future ticker.
        """
        futures_chain_tickers_df = self._data_provider.get_futures_chain_tickers(self,
                                                                                 ExpirationDateField.all_dates())[self]
        # Get the minimum date
        futures_chain_tickers_series = futures_chain_tickers_df.min(axis=1)

        # Filter out the non-designated contracts
        month_codes = "|".join(self.designated_contracts)
        contracts_pattern = self.family_id.format(f"({month_codes})\\d{{1,2}}")
        designated_contracts = futures_chain_tickers_series.index[
            futures_chain_tickers_series.index.map(lambda t: bool(re.search(f"^{contracts_pattern}$", t.as_string())))]
        futures_chain_tickers_series = futures_chain_tickers_series.loc[designated_contracts]

        futures_chain_tickers = QFSeries(futures_chain_tickers_series.index, futures_chain_tickers_series.values)
        futures_chain_tickers.index = to_datetime(futures_chain_tickers.index)
        return futures_chain_tickers

    def belongs_to_family(self, ticker: BloombergTicker) -> bool:
        """
        Function, which takes a specific BloombergTicker, verifies if it belongs to the family of futures contracts,
        identified by the BloombergFutureTicker and returns true if that is the case (false otherwise).
        """
        pattern = self.family_id.format("[A-Z]\\d{1,2}")
        return bool(re.match(f"^{pattern}$", ticker.ticker)) and \
            (ticker.point_value, ticker.security_type) == (self.point_value, self.security_type)

    def supported_ticker_type(self) -> Type[Ticker]:
        return BloombergTicker
