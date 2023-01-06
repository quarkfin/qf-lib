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
from datetime import datetime
from typing import Optional, Type

import pandas as pd

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.series.qf_series import QFSeries


class FutureTicker(Ticker, metaclass=abc.ABCMeta):
    """Class to represent a Ticker, which gathers multiple future contracts.

    The FutureTicker class extends the standard Ticker class. It allows the user to use only a Ticker abstraction,
    which provides all of the standard Ticker functionalities (e.g. just as standard tickers, it can be used along with
    DataHandler functions get_price, get_last_available_price, get_current_price etc.), without the need to manually
    manage the rolling of the contracts or to select a certain specific Ticker.

    Notes
    ------
    While downloading historical data (using for example get_price function) all of the prices would be provided for
    the current specific ticker, e.g. in case of the family of Cotton future contracts, if on a certain day the
    specific contract returned by the FutureTicker will be the December 2019 Cotton contract, all of the prices
    returned by get_price will pertain to this specific December contract and no prices chaining will occur.
    In order to use the get_price function along with futures contracts chaining (and eventual adjustments),
    the FuturesChain object has to be used.

    Parameters
    -----------
    name: str
        Field which contains a name (or a short description) of the FutureTicker.
    family_id: str
        Identificator used to describe the whole family of future contracts. In case of specific Future Tickers
        its purpose is to build an identificator, used by the data provider to download the chain of corresponding
        Tickers, and to verify whether a specific Ticker belongs to a certain futures family.
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
        DataProvider get_futures_chain_tickers function.
    """
    def __init__(self, name: str, family_id: str, N: int, days_before_exp_date: int, point_value: int = 1,
                 designated_contracts: Optional[str] = None, security_type: SecurityType = SecurityType.FUTURE):
        super().__init__(family_id, security_type, point_value)
        self._name = name
        self.family_id = family_id
        self.point_value = point_value
        self.N = N
        self.designated_contracts = designated_contracts

        self._days_before_exp_date = days_before_exp_date

        self._exp_dates = None  # type: QFSeries
        self._timer = None  # type: Timer
        self._data_provider = None  # type: "DataProvider"
        self._ticker_initialized = False  # type: bool

        # Date used for optimization purposes
        self._ticker = None  # type: Ticker
        self._last_cached_datetime = None
        self._expiration_hour = RelativeDelta(hour=0, minute=0, second=0, microsecond=0)

    def initialize_data_provider(self, timer: Timer, data_provider: "DataProvider"):
        """ Initialize the future ticker with data provider and ticker.

        Parameters
        ----------
        timer: Timer
            Timer which is used further when computing the current ticker.
        data_provider: DataProvider
            Data provider which is used to download symbols of tickers, belonging to the given future ticker family
        """
        if self._ticker_initialized:
            self.logger.warning(f"The FutureTicker {self._name} has been already initialized with Timer and Data "
                                f"Provider. The previous Timer and Data Provider references will be overwritten")

        self._data_provider = data_provider
        self._timer = timer

        # Download and validate expiration dates for the future ticker
        exp_dates = self._get_futures_chain_tickers()
        self._validate_expiration_dates(exp_dates)
        self._exp_dates = exp_dates

        self._ticker_initialized = True

    @property
    def ticker(self) -> str:
        """
        Property which returns the value of 'ticker' attribute of the currently valid, specific Ticker.
        E.g. in case of Cotton FutureTicker in the beginning of December, before the expiration date of December ticker,
        the function will return the Ticker("CTZ9 Comdty").ticker string value.

        Returns
        -------
        str
            String of the current specific ticker.
        """
        return self.get_current_specific_ticker().ticker

    @property
    def name(self) -> str:
        """
        Returns the name of the future ticker.
        """
        return self._name

    def get_current_specific_ticker(self) -> Ticker:
        """
        Method which returns the currently valid, specific Ticker.

        In order to optimize the computation of ticker value the ticker value is being cached.
        The ticker is assumed to expire at a given expiration hour (which can be adjusted using the set_expiration_hour,
        by default it points to midnight), which means that on the expiration date the old contract is returned till
        the expiration hour and the new contract is returned since the expiration hour (inclusive).

        Returns
        -------
        Ticker
            The current specific ticker.
        """

        # If the timer or data provider were not set
        if not self._ticker_initialized:
            raise ValueError(f"Set up the timer and data provider by calling initialize_data_provider() "
                             f"before using the future ticker {self._name}")
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
                _exp_dates = _exp_dates.sort_index()
                date_index = _exp_dates.index - pd.Timedelta(days=self._days_before_exp_date - 1)
                date_index = pd.DatetimeIndex([dt + self._expiration_hour for dt in date_index])
                date_index_loc = date_index.get_indexer([self._timer.now()], method="pad")[0]
                return _exp_dates.iloc[date_index_loc:].iloc[self.N]

            def cached_ticker_still_valid(caching_time: datetime, current_time: datetime,
                                          expiration_hour: RelativeDelta) -> bool:
                """
                Checks if the precomputed specific ticker value is still valid or should be computed once again.
                The cached value is valid for 24h starting at the expiration_hour (e.g. if the expiration hour is
                set to 8:00, a specific ticker is valid starting 8:00 am (inclusive) till 8.00 am the next day).
                """
                if caching_time is None:
                    return False

                if caching_time >= caching_time + expiration_hour:
                    cached_time_start = caching_time + expiration_hour
                    cached_time_end = cached_time_start + RelativeDelta(days=1)
                else:
                    cached_time_end = caching_time + expiration_hour
                    cached_time_start = cached_time_end - RelativeDelta(days=1)

                return cached_time_start <= current_time < cached_time_end

            if not cached_ticker_still_valid(self._last_cached_datetime, self._timer.now(), self._expiration_hour):
                self._ticker = _get_current_specific_ticker()
                self._last_cached_datetime = self._timer.now()
            return self._ticker

        except (LookupError, ValueError):
            # Function "get_loc(self.timer.now(), method="pad")" may raise KeyError in case if e.g. the current time
            # precedes the first date in the shifted_index.
            # Function "iloc" may rise IndexError if the requested indexer is out-of-bonds (e.g. a high value of self.N)
            # Therefore, in case if the data with expiration dates is not available for the current date, the
            # _get_current_specific_ticker function will raise a LookupError.
            raise NoValidTickerException(f"No valid ticker for the FutureTicker {self._name} found on "
                                         f"{self._timer.now()}") from None

    def get_expiration_dates(self) -> QFSeries:
        """
        Returns QFSeries containing the list of specific future contracts Tickers, indexed by their expiration
        dates. The index contains original expiration dates, as returned by the data handler, without shifting it by the
        days_before_exp_date days (it is important to store the original values, instead of shifted ones, as this
        function is public and used by multiple other components).

        Returns
        --------
        QFSeries
            QFSeries containing the list of specific future contracts Tickers, indexed by their expiration dates
        """
        return self._exp_dates

    def get_N(self):
        return self.N

    def get_days_before_exp_date(self):
        return self._days_before_exp_date

    def set_expiration_hour(self, hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0):
        """ Sets the expiration hour. Expiration hour is used to compute the current specific ticker. By default the
        expiration hour is set to midnight, which means that within one day always the same current specific ticker is
        returned.

        In case if the expiration hour is set to 8:00 pm then if that day was the last day the contract was
        valid, then the new contract is returned since 8:00 pm that day (inclusive).

        Parameters
        ----------
        hour: int
        minute: int
        second: int
        microsecond: int
        """
        self._expiration_hour = RelativeDelta(hour=hour, minute=minute, second=second, microsecond=microsecond)

    @abc.abstractmethod
    def _get_futures_chain_tickers(self) -> QFSeries:
        """
        Returns the QFSeries with specific Tickers, indexed by their expiration dates.
        Each class, inheriting from the Future Ticker has to implement some strategy of obtaining  the expiration dates
        from the available fields (e.g. first notice, last tradeable date etc.)
        """
        pass

    def _validate_expiration_dates(self, expiration_dates: QFSeries):
        """ Raises an error in case if the expiration dates series is invalid. """
        if any(expiration_dates.index.duplicated()):
            duplicated_rows = expiration_dates.loc[expiration_dates.index.duplicated(keep=False)]
            raise ValueError(f"The Expiration Dates for ticker {self} contain duplicated dates for the following "
                             f"contracts: \n{duplicated_rows}\n"
                             f"In order to fix this issue you can skip some of the contract months using the "
                             f"designated_contracts parameter of the {self.__class__.__name__}.")

        # Make sure that all the tickers have the correct point_value and security type
        if any([ticker.point_value != self.point_value for ticker in expiration_dates.values]):
            raise ValueError(f"Not all tickers in the chain have the point_value set to {self.point_value} as the "
                             f"Future Ticker. Please make sure that correct values are inserted by the DataProvider "
                             f"and _get_futures_chain_tickers() function.")

        if any([ticker.security_type != self.security_type for ticker in expiration_dates.values]):
            raise ValueError(f"Not all tickers in the chain have the point_value set to {self.point_value} as the "
                             f"Future Ticker. Please make sure that correct values are inserted by the DataProvider "
                             f"and _get_futures_chain_tickers() function.")

    @ticker.setter
    def ticker(self, _):
        # The purpose of this function is to enable the initial setting of ticker value, in the __init__ function.
        pass

    @property
    def initialized(self) -> bool:
        """ Boolean providing information on whether the data provider and timer were set for this Future Ticker
        instance or not. """
        return self._ticker_initialized

    def __repr__(self):
        return self._get_str_repr()

    def __str__(self):
        return self._get_str_repr()

    def _get_str_repr(self):
        return f"{self.__class__.__name__}('{self._name}', '{self.family_id}')"

    def __eq__(self, other):
        if other is self:
            return True

        if not isinstance(other, FutureTicker):
            return False

        return self is other or (
                type(self) == type(other)
                and self._name == other.name
                and self.family_id == other.family_id
                and self.point_value == other.point_value
                and self.N == other.get_N()
                and self._days_before_exp_date == other.get_days_before_exp_date()
        )

    def __hash__(self):
        return hash((self._name, self.family_id, type(self), self.point_value, self.N, self._days_before_exp_date))

    def __lt__(self, other):
        if not isinstance(other, FutureTicker):
            if isinstance(other, Ticker):
                return super().__lt__(other)
            else:
                raise TypeError("Cannot compare this object with a FutureTicker")

        class_name = self.__class__.__name__
        other_class_name = other.__class__.__name__

        return (class_name, self._name, self.family_id, self.N, self._days_before_exp_date) < \
               (other_class_name, other.name, other.family_id, other.get_N(), other.get_days_before_exp_date())

    def __getstate__(self):
        """
        In order to avoid issues while pickling Future Tickers set its data provider and timer to None and require
        reinitialization afterwards.
        """
        self.logger = None
        self._data_provider = None
        self._timer = None
        self._ticker_initialized = False
        return self.__dict__

    @abc.abstractmethod
    def belongs_to_family(self, ticker: Ticker) -> bool:
        """
        Function, which takes a specific Ticker, and verifies if it belongs to the family of futures contracts,
        identified by the FutureTicker.

        Returns
        -------
        bool
        """
        pass

    @abc.abstractmethod
    def supported_ticker_type(self) -> Type[Ticker]:
        """
        Returns class of specific tickers which are supported by this FutureTicker (e.g. it should return
        BloombergTicker for the BloombergFutureTicker etc.
        """
        pass
