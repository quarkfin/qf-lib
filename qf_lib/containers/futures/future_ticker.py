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
import abc
import re

import pandas as pd

from qf_lib.common.tickers.tickers import Ticker, BloombergTicker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.qf_series import QFSeries


class FutureTicker(Ticker, metaclass=abc.ABCMeta):
    def __init__(self, ticker: str, family_id: str, timer: Timer, data_handler: "DataHandler", N: int,
                 days_before_exp_date: int, point_value: float = 1.0):

        super().__init__(ticker)
        self.family_id = family_id
        self.point_value = point_value
        self.N = N
        self.days_before_exp_date = days_before_exp_date

        self._timer = timer
        self.data_handler = data_handler
        self._exp_dates = None  # type: QFSeries

        # Date used for optimization purposes
        self._last_cached_day = None
        self._ticker = None  # type: str

    @property
    def ticker(self) -> str:
        """
        Property which returns the value of 'ticker' attribute of the currently valid, specific Ticker.

        E.g. in case of Cotton FutureTicker in the beginning of December, before the expiration date of December ticker,
        the function will return the Ticker("CTZ9 Comdty").ticker string value.
        """
        return self.valid_ticker().ticker

    def as_string(self) -> str:
        """
        Returns a string representation of a ticker
        """
        try:
            return self.ticker
        except (AttributeError, KeyError):
            return None

    def valid_ticker(self) -> Ticker:
        """
        Property which returns the value of 'ticker' attribute of the currently valid, specific Ticker.

        E.g. in case of Cotton FutureTicker in the beginning of December, before the expiration date of December ticker,
        the function will return the Ticker("CTZ9 Comdty").ticker string value.

        In order to optimize the computation of ticker value, as the contracts are assumed not to expire within
        the day (they can expire only at 0:00 a.m.), the ticker value is being cached for a certain day. If the function
        will be called for a date, for which the ticker value was already computed once, the cached value is being
        returned.
        """
        def get_current_ticker() -> Ticker:
            """
            Returns the ticker of N-th Future Contract for the provided date, assuming that days_before_exp_date days
            before the original expiration the ticker of the next contract will be returned.
            E.g. if days_before_exp_date = 4 and the expiry date = 16th July, then the old contract will be returned up
            to 16 - 4 = 12th July (inclusive).
            """
            # Shift the index and data according to the start time and end time values
            date_index = self._exp_dates.index - pd.Timedelta(days=self.days_before_exp_date - 1)
            date_index_loc = date_index.get_loc(self._timer.now(), method="pad")
            return self._exp_dates.iloc[date_index_loc:].iloc[self.N]

        try:
            if self._last_cached_day is not self._timer.now().date():
                self._ticker = get_current_ticker()
                self._last_cached_day = self._timer.now().date()

        except (AttributeError, LookupError):
            # AttributeError may be raised in case if self._exp_dates is not initialized yet adn thus has no attribute
            # "index".
            # Function "get_loc(self._timer.now(), method="pad")" may raise KeyError in case if e.g. the current time
            # precedes the first date in the shifted_index.
            # Function "iloc" may rise IndexError if the requested indexer is out-of-bonds (e.g. a high value of self.N)
            # Therefore, in case if the data with expiration dates is not available for the current date, the
            # get_current_ticker function will raise either AttributeError or a LookupError.

            # In case of not being able to get the current value of the ticker, download the necessary data
            self._exp_dates = self._get_futures_chain_tickers()
            self._ticker = get_current_ticker()
            self._last_cached_day = self._timer.now().date()

        return self._ticker

    def _get_futures_chain_tickers(self):
        futures_chain_tickers = self.data_handler.get_futures_chain_tickers(self, self._timer.now())[self]
        # Filter out the non Tickers from the Series
        valid_tickers = futures_chain_tickers[futures_chain_tickers.apply(lambda ticker: isinstance(ticker, Ticker))]
        return valid_tickers

    def get_expiration_dates(self):
        try:
            date_index = self._exp_dates.index - pd.Timedelta(days=self.days_before_exp_date - 1)
            if date_index[-2] <= self._timer.now():
                self._exp_dates = self._get_futures_chain_tickers()
        except (AttributeError, IndexError):
            self._exp_dates = self._get_futures_chain_tickers()

        return self._exp_dates

    @ticker.setter
    def ticker(self, _):
        # The purpose of this function is to enable the initial setting of ticker value, in the __init__ function.
        pass

    def __eq__(self, other):
        return self is other or (
                type(self) == type(other)
                and self.family_id == other.family_id
                and self.point_value == other.point_value
                and self.N == other.N
                and self.days_before_exp_date == other.days_before_exp_date
        )

    def __hash__(self):
        return hash((self.family_id, type(self), self.point_value, self.N, self.days_before_exp_date))

    def __lt__(self, other):
        if not isinstance(other, FutureTicker):
            if isinstance(other, Ticker):
                return super().__lt__(other)
            else:
                raise TypeError("Cannot compare this object with a FutureTicker")

        class_name = self.__class__.__name__
        other_class_name = other.__class__.__name__

        return (class_name, self.family_id, self.N, self.days_before_exp_date) < \
               (other_class_name, other.family_id, other.N, other.days_before_exp_date)

    @abc.abstractmethod
    def belongs_to_family(self, ticker: Ticker) -> bool:
        pass


class BloombergFutureTicker(FutureTicker, BloombergTicker):
    def __init__(self, ticker: str, family_id: str, timer: Timer, data_handler: "DataHandler", N: int,
                 days_before_exp_date: int, point_value: float = 1.0, designated_contracts: str = "FGHJKMNQUVXZ"):
        """
        designated_contracts is a string, which represents all month codes, that are being downloaded and stored
        in the chain of future contracts. Any specific order of letters is not required. E.g. providing this
        parameter value equal to "HMUZ", would restrict the future chain to only the contracts, which expire in
        March, June, September and December, even if contracts for any other months exist and are returned by the
        BloombergDataProvider get_futures_chain_tickers function.
        """
        self.designated_contracts = designated_contracts
        if not len(designated_contracts) > 0:
            raise ValueError("At least one month code should be provided.")

        super().__init__(ticker, family_id, timer, data_handler, N, days_before_exp_date, point_value)

    def get_specific_ticker(self):
        seed = self.designated_contracts[-1] + '9'
        specific_ticker_string = self.family_id.format(seed)
        return BloombergTicker.from_string(specific_ticker_string)

    def _get_futures_chain_tickers(self):
        """
        Function used to download the expiration dates of the futures contracts, in order to return afterwards current
        futures tickers. It uses the list of month codes of designated contracts and filter out these, that should not
        be considered by the future ticker.
        """
        futures_chain_tickers = super()._get_futures_chain_tickers()

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
