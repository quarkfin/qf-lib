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

import logging
from abc import abstractmethod, ABCMeta
from functools import total_ordering
from os.path import basename
from typing import Union, Sequence, Tuple, List, Optional

from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


@total_ordering
class Ticker(metaclass=ABCMeta):
    """Representation of a security.

    Parameters
    --------------
    ticker: str
        identifier of the security in a specific database
    """
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def __str__(self):
        return "{}:{}".format(self.__class__.__name__, self.ticker)

    def __repr__(self):
        return "{}:{}".format(self.__class__.__name__, self.ticker)

    def as_string(self) -> str:
        """
        Returns a string representation of a ticker
        """
        return self.ticker

    @abstractmethod
    def from_string(self, ticker_str: Union[str, Sequence[str]]) -> Union['Ticker', Sequence['Ticker']]:
        """allows creation of a ticker from a string"""

    def __eq__(self, other):
        return self is other or (
            isinstance(self, type(other)) and
            self.ticker == other.ticker
        )

    def __lt__(self, other):
        if not isinstance(other, Ticker):
            raise TypeError("Cannot compare this object with a Ticker")

        class_name = self.__class__.__name__
        other_class_name = other.__class__.__name__

        return (class_name, self.ticker) < (other_class_name, other.ticker)

    def __hash__(self):
        return hash((self.ticker, type(self)))

    def __getstate__(self):
        self.logger = None
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
        self.logger = qf_logger.getChild(self.__class__.__name__)


class BloombergTicker(Ticker):
    """Representation of bloomberg tickers."""
    def __init__(self, ticker: str):
        super().__init__(ticker)

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]]) \
            -> Union["BloombergTicker", Sequence["BloombergTicker"]]:
        """
        Example: BloombergTicker.from_string('SPX Index')
        """
        if isinstance(ticker_str, str):
            return BloombergTicker(ticker_str)
        else:
            return [BloombergTicker(t) for t in ticker_str]


class InternalDBTicker(Ticker):
    """Representation of tickers inside the database.

    Parameters
    ------------
    ticker: int, str
       string is either timeseriesID or 'timeseriesName'
       for example 123 or 'My Strategy Name'
       if ticker is int - it corresponds to the ID of the timeseries in the DB
       if ticker is str - it corresponds to the timeseries name
   """
    def __init__(self, ticker: Union[int, str]):
        assert isinstance(ticker, (int, str)), "Ticker value must be either series name (string) or series id (int)"
        super().__init__(ticker)

    def as_string(self) -> str:
        return '#' + str(self.ticker)

    @classmethod
    def from_string(cls, ticker_str: Union[str, int, Sequence[Union[str, int]]]) \
            -> Union["InternalDBTicker", Sequence["InternalDBTicker"]]:
        """
        Example: InternalDBTicker.from_string('#TimeseriesName')
        Example: InternalDBTicker.from_string('#123')
        """

        def to_ticker(ticker_string: str):
            clean_str = ticker_string[1:]  # skip '#'
            try:
                integer_value = int(clean_str)
                return InternalDBTicker(integer_value)
            except ValueError:
                return InternalDBTicker(clean_str)

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]


class HaverTicker(Ticker):
    """Haver tickers representation. For example E025RE@EUSRVYS -> ticker: E025RE, EUSRVYS: database_name

    Parameters
    ------------
    ticker: str
        string containing series ID within a specific database
    database_name: str
        name of the database where the series is located
    """
    def __init__(self, ticker: str, database_name: str):
        super().__init__(ticker)
        self.database_name = database_name

    def as_string(self) -> str:
        """
        returns a string that can be used by the official Haver API to get the series
        """
        return self.ticker + '@' + self.database_name

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]]) -> Union["HaverTicker", Sequence["HaverTicker"]]:
        """
        Example: HaverTicker.from_string('RECESSQ2@USECON')
        """

        def to_ticker(ticker_string: str):
            ticker, db_name = ticker_string.split('@')
            return HaverTicker(ticker, db_name)

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]


class QuandlTicker(Ticker):
    """Representation of Quandl tickers."""
    def __init__(self, ticker: str, database_name: str, database_type: QuandlDBType = QuandlDBType.Timeseries):
        super().__init__(ticker)
        self.database_name = database_name
        self.database_type = database_type

    def as_string(self) -> str:
        if self.database_type == QuandlDBType.Timeseries:
            # returns a string that corresponds to the notation used by Quandl Timeseries: db_name/ticker
            return self.database_name + '/' + self.ticker
        elif self.database_type == QuandlDBType.Table:
            return self.ticker
        else:
            raise TypeError("Incorrect database type: {}".format(self.database_type))

    def field_to_column_name(self, field: str):
        return self.as_string() + ' - ' + field

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]], db_type: QuandlDBType = QuandlDBType.Timeseries) \
            -> Union["QuandlTicker", Sequence["QuandlTicker"]]:
        """
        Example: QuandlTicker.from_string('WIKI/MSFT')
        Note: this method supports only the Timeseries tickers at the moment.
        """

        def to_ticker(ticker_string: str):
            db_name, ticker = ticker_string.rsplit('/', 1)
            return QuandlTicker(ticker, db_name, db_type)

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]


class CcyTicker(Ticker):
    """Representation of Cryptocurrency tickers.

    Parameters
    ------------
    ticker: str
        The name of the crypto currency. For example Bitcoin -> ticker: bitcoin

    """
    def __init__(self, ticker: str):
        super().__init__(ticker)

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]]) -> Union["CcyTicker", Sequence["CcyTicker"]]:
        """
        Example: CcyTicker.from_string('Bitcoin')
        """

        def to_ticker(ticker_string: str):
            return CcyTicker(ticker_string.lower())

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]


def tickers_as_strings(tickers: Union[Ticker, Sequence[Ticker]]) -> Union[str, List[str]]:
    """
    Converts a single ticker or sequence of tickers to strings representations.
    if single ticker is passed -> returns a single string
    if sequence of tickers is passed -> returns list of strings
    """
    if isinstance(tickers, Ticker):
        return tickers.as_string()
    else:
        return [t.as_string() for t in tickers]


def str_to_ticker(ticker_str: Union[str, Sequence[str]]) -> Union[None, Ticker, Tuple[List[Ticker], List[str]]]:
    """
    Converts a single string or sequence of strings to ticker representation.

    if single ticker is passed -> returns single_ticker or None

    if sequence of tickers is passed -> returns a tuple
        (successfully converted tickers, unsuccessfully converted tickers)
        If all tickers were successfully converted the second list should be empty

    """

    def convert_single_ticker(single_ticker_str: str) -> Optional[Ticker]:
        if single_ticker_str[0] == "#":
            return InternalDBTicker.from_string(single_ticker_str)
        elif "@" in single_ticker_str:
            return HaverTicker.from_string(single_ticker_str)
        elif " " in single_ticker_str:
            return BloombergTicker.from_string(single_ticker_str)
        elif "/" in single_ticker_str:
            return QuandlTicker.from_string(single_ticker_str)
        else:
            return None

    logger = logging.getLogger(basename(__file__))
    if isinstance(ticker_str, str):
        ticker = convert_single_ticker(ticker_str)
        if ticker is None:
            logger.warning("Value '{}' cannot be recognised as a ticker".format(ticker_str))
        return ticker
    else:
        successful_tickers = []
        unsuccessful_tickers = []

        for t in ticker_str:
            ticker = convert_single_ticker(t)
            if ticker is not None:
                successful_tickers.append(ticker)
            else:
                unsuccessful_tickers.append(t)

        if unsuccessful_tickers:
            for faulty_ticker in unsuccessful_tickers:
                logger.warning("Value '{}' cannot be recognised as a ticker".format(faulty_ticker))

        return successful_tickers, unsuccessful_tickers


def ticker_type_to_class(ticker_type: str):
    """
    Takes name of a specific Ticker class (e.g. "BloombergTicker") and returns a corresponding Ticker object.
    """
    mapping = {
        'BloombergTicker': BloombergTicker,
        'InternalDBTicker': InternalDBTicker,
        'HaverTicker': HaverTicker,
        'QuandlTicker': QuandlTicker,
        'CcyTicker': CcyTicker
    }

    return mapping[ticker_type]
