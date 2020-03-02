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

import pandas as pd

from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.qf_series import QFSeries


class FutureTicker(Ticker, metaclass=abc.ABCMeta):
    def __init__(self, name: str, family_id: str, N: int, days_before_exp_date: int, point_value: float = 1.0):
        """
        name
            Field which contains a name (or a short description) of the FutureTicker.
        family_id
            Identificator used to describe the whole family of future contracts. In case of specific Future Tickers
            its purpose is to build an identificator, used by the data provider to download the chain of corresponding
            Tickers, and to verify whether a specific Ticker belongs to a certain futures family.
        N
            Used to identify which specific Ticker should be considered by the Backtester, while using the general
            Future Ticker class. For example N parameter set to 1, denotes the front future contract.
        days_before_exp_date
            Number of days before the expiration day of each of the contract, when the “current” specific contract
            should be substituted with the next consecutive one.
        point_value
            Used to define the size of the contract.
        """

        super().__init__(family_id)
        self.name = name
        self.family_id = family_id
        self.point_value = point_value
        self._N = N
        self._days_before_exp_date = days_before_exp_date

        self._exp_dates = None  # type: QFSeries
        self._timer = None  # type: Timer
        self._data_provider = None  # type: "DataProvider"
        self._ticker_initialized = False

        # Date used for optimization purposes
        self._ticker = None  # type: Ticker
        self._last_cached_date = None

    def initialize_data_provider(self, timer: Timer, data_provider: "DataProvider"):
        if self._ticker_initialized:
            self.logger.warning("The FutureTicker {} has been already initialized with Timer and Data Provider. "
                                "The previous Timer and Data Provider references will be overwritten".format(self.name))

        self._data_provider = data_provider
        self._timer = timer
        self._exp_dates = self._get_futures_chain_tickers()
        self._ticker_initialized = True

    @property
    def ticker(self) -> str:
        """
        Property which returns the value of 'ticker' attribute of the currently valid, specific Ticker.

        E.g. in case of Cotton FutureTicker in the beginning of December, before the expiration date of December ticker,
        the function will return the Ticker("CTZ9 Comdty").ticker string value.
        """
        return self.get_current_specific_ticker().ticker

    def get_current_specific_ticker(self) -> Ticker:
        """
        Method which returns the currently valid, specific Ticker.

        In order to optimize the computation of ticker value, as the contracts are assumed not to expire within
        the day (they can expire only at 0:00 a.m.), the ticker value is being cached for a certain date.
        If the function will be called for a date, for which the ticker value was already computed once, the cached
        value is being returned.
        """

        try:
            def _get_current_specific_ticker() -> Ticker:
                """
                Returns the ticker of N-th Future Contract for the provided date, assuming that days_before_exp_date
                days before the original expiration the ticker of the next contract will be returned.
                E.g. if days_before_exp_date = 4 and the expiry date = 16th July, then the old contract will be returned
                up to 16 - 4 = 12th July (inclusive).
                """
                # Shift the index and data according to the start time and end time values
                _exp_dates = self.get_expiration_dates()
                date_index = _exp_dates.index - pd.Timedelta(days=self._days_before_exp_date - 1)
                date_index_loc = date_index.get_loc(self._timer.now(), method="pad")
                return _exp_dates.iloc[date_index_loc:].iloc[self._N]

            # If the timer or data provider were not set
            if not self._ticker_initialized:
                raise ValueError("Set up the timer and data provider by calling initialize_data_provider() "
                                 "before using the future ticker {}".format(self.name))

            if self._last_cached_date != self._timer.now().date():
                self._ticker = _get_current_specific_ticker()
                self._last_cached_date = self._timer.now().date()
            return self._ticker

        except LookupError:
            # Function "get_loc(self._timer.now(), method="pad")" may raise KeyError in case if e.g. the current time
            # precedes the first date in the shifted_index.
            # Function "iloc" may rise IndexError if the requested indexer is out-of-bonds (e.g. a high value of self.N)
            # Therefore, in case if the data with expiration dates is not available for the current date, the
            # _get_current_specific_ticker function will raise a LookupError.

            raise NoValidTickerException("No valid ticker for the FutureTicker found on {}".format(
                self.name,
                self._timer.now()
            ))

    def get_expiration_dates(self):
        """
        Returns the QFSeries containing the list of specific future contracts Tickers, indexed by their expiration
        dates. The index contains original expiration dates, as returned by the data handler, without shifting it by the
        days_before_exp_date days (it is important to store the original values, instead of shifted ones, as this
        function is public and used by multiple other components).
        """
        return self._exp_dates

    def get_N(self):
        return self._N

    def get_days_before_exp_date(self):
        return self._days_before_exp_date

    def _get_futures_chain_tickers(self):
        """
        Returns the QFSeries with specific Tickers, indexed by their expiration dates.
        """
        futures_chain_tickers = self._data_provider.get_futures_chain_tickers(self)[self]
        return futures_chain_tickers

    @ticker.setter
    def ticker(self, _):
        # The purpose of this function is to enable the initial setting of ticker value, in the __init__ function.
        pass

    def __eq__(self, other):
        return self is other or (
                type(self) == type(other)
                and self.name == other.name
                and self.family_id == other.family_id
                and self.point_value == other.point_value
                and self._N == other.get_N()
                and self._days_before_exp_date == other.get_days_before_exp_date()
        )

    def __hash__(self):
        return hash((self.name, self.family_id, type(self), self.point_value, self._N, self._days_before_exp_date))

    def __lt__(self, other):
        if not isinstance(other, FutureTicker):
            if isinstance(other, Ticker):
                return super().__lt__(other)
            else:
                raise TypeError("Cannot compare this object with a FutureTicker")

        class_name = self.__class__.__name__
        other_class_name = other.__class__.__name__

        return (class_name, self.name, self.family_id, self._N, self._days_before_exp_date) < \
               (other_class_name, other.name, other.family_id, other.get_N(), other.get_days_before_exp_date())

    @abc.abstractmethod
    def belongs_to_family(self, ticker: Ticker) -> bool:
        """
        Function, which takes a specific Ticker, and verifies if it belongs to the family of futures contracts,
        identified by the FutureTicker.
        """
        pass


