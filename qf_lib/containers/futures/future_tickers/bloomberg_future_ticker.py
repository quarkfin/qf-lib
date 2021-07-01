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
import pandas as pd
import re

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.tickers.tickers import BloombergTicker
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
        Used to identify which specific Ticker should be considered by the Backtester, while using the general
        Future Ticker class. For example N parameter set to 1, denotes the front future contract.
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
    """
    def __init__(self, name: str, family_id: str, N: int, days_before_exp_date: int, point_value: int = 1,
                 designated_contracts: str = "FGHJKMNQUVXZ"):
        self.designated_contracts = designated_contracts
        if not len(designated_contracts) > 0:
            raise ValueError("At least one month code should be provided.")

        super().__init__(name, family_id, N, days_before_exp_date, point_value)

    def get_active_ticker(self) -> BloombergTicker:
        """ Returns the active ticker. """
        specific_ticker_string = self.family_id.format("A")
        return BloombergTicker.from_string(specific_ticker_string)

    def _get_futures_chain_tickers(self):
        """
        Function used to download the expiration dates of the futures contracts, in order to return afterwards current
        futures tickers. It uses the list of month codes of designated contracts and filter out these, that should not
        be considered by the future ticker.
        """
        futures_chain_tickers_df = self._data_provider.get_futures_chain_tickers(self,
                                                                                 ExpirationDateField.all_dates())[self]
        # Get the minimum date
        futures_chain_tickers = futures_chain_tickers_df.min(axis=1)
        futures_chain_tickers = QFSeries(data=futures_chain_tickers.index, index=futures_chain_tickers.values)
        futures_chain_tickers.index = pd.to_datetime(futures_chain_tickers.index)

        # Filter out the non-designated contracts
        seed = self.family_id.split("{}")[0]
        designated_contracts_seeds = tuple(seed + month_code for month_code in self.designated_contracts)
        futures_chain_tickers = futures_chain_tickers[futures_chain_tickers.apply(
            lambda t: t.ticker.startswith(designated_contracts_seeds)
        )]
        return futures_chain_tickers

    def belongs_to_family(self, specific_ticker: BloombergTicker) -> bool:
        """
        Function, which takes a specific BloombergTicker, and verifies if it belongs to the family of futures contracts,
        identified by the FutureTicker.

        Returns
        -------
        bool
        """
        def ticker_to_family_id(t: BloombergTicker) -> str:
            """
            Returns a custom ID, used to identify futures contracts families.

            The function parses the contract symbol string and substitutes the characters which identify the month
            (1 letter) and year of contract expiration (1-2 digits at the end of the first word in the string) with the
            {} placeholder, e.g. in case of 'CTH16 Comdty', it returns 'CT{} Comdty'.
            """
            groups = re.search(r'^.+([A-Z]\d{1,2}) \.*', t.ticker).groups()
            month_year_part = groups[0]
            return t.ticker.replace(month_year_part, "{}")

        try:
            family_id = ticker_to_family_id(specific_ticker)
            return self.family_id == family_id
        except AttributeError:
            return False
