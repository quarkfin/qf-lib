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

from abc import abstractmethod, ABCMeta
from functools import total_ordering
from typing import Union, Sequence

from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


@total_ordering
class Ticker(metaclass=ABCMeta):
    """Representation of a security.

    Parameters
    --------------
    ticker: str
        identifier of the security in a specific database
    security_type: SecurityType
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc.
    point_value: int
        size of the contract as given by the ticker's Data Provider.
    """
    def __init__(self, ticker: str, security_type: SecurityType, point_value: int):
        self.ticker = ticker
        self.security_type = security_type
        self.point_value = point_value
        self._name = ticker

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def __str__(self):
        return "{}('{}')".format(self.__class__.__name__, self.ticker)

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.ticker)

    def as_string(self) -> str:
        """
        Returns a string representation of a ticker
        """
        return self.ticker

    @property
    def name(self) -> str:
        """
        Returns a name of the ticker.
        The property should be adjusted for different Ticker classes to provide a string representation of a Ticker,
        which in some cases could be more understandable than the output of as_string() function.
        """
        return self._name

    def set_name(self, name: str):
        """ Sets the name of the ticker. Name should be used for different Ticker classes to provide a readable string
        representation of a Ticker. For example, for tickers of security type FUTURE it is a good idea to set the name
        to point to the name of the asset (e.g. Cotton, Corn) to faciliate the further analysis of the tickers in
        transactions, portfolio etc. """
        self._name = name

    @abstractmethod
    def from_string(self, ticker_str: Union[str, Sequence[str]]) -> Union['Ticker', Sequence['Ticker']]:
        """ Allows creation of a ticker from a string """
        pass

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
    """ Representation of Bloomberg tickers.

    Parameters
    --------------
    ticker: str
        identifier of the security, e.g. 'CTZ9 Comdty' or 'MSFT US Equity'
    security_type: SecurityType
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc. By default equals SecurityType.STOCK.
    point_value: int
        size of the contract as given by the ticker's Data Provider. Used mostly by tickers of security_type FUTURE and
        by default equals 1.
    """
    def __init__(self, ticker: str, security_type: SecurityType = SecurityType.STOCK, point_value: int = 1):
        super().__init__(ticker, security_type, point_value)

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.STOCK,
                    point_value: int = 1) -> Union["BloombergTicker", Sequence["BloombergTicker"]]:
        """
        Example: BloombergTicker.from_string('SPX Index')
        """
        if isinstance(ticker_str, str):
            return BloombergTicker(ticker_str, security_type, point_value)
        else:
            return [BloombergTicker(t, security_type, point_value) for t in ticker_str]


class PortaraTicker(Ticker):
    """ Representation of Portara tickers.

    Parameters
    --------------
    ticker: str
        identifier of the security, e.g. 'SI2012Z'. The naming convention used to generate the data in Portara should
        be the "SymYYYYM".
    security_type: SecurityType
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc.
    point_value: int
        size of the contract as given by the Portara (e.g. 50 for Silver future contracts).
    """
    def __init__(self, ticker: str, security_type: SecurityType, point_value):
        super().__init__(ticker, security_type, point_value)

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.STOCK,
                    point_value: int = 1) -> Union["PortaraTicker", Sequence["PortaraTicker"]]:
        if isinstance(ticker_str, str):
            return PortaraTicker(ticker_str, security_type, point_value)
        else:
            return [PortaraTicker(t, security_type, point_value) for t in ticker_str]


class BinanceTicker(Ticker):
    """ Representation of Binance tickers.

    Parameters
    --------------
    currency:
        identifier of the security, e.g. 'BTC'
    quote_ccy:
        the quote currency of the asset.
        For example to trade BTC using USDT use:
            BTC as currency
            USDT as quote_ccy
        quote currency here should be the same as quote_ccy set in BinanceContractTickerMapper
    security_type:
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc. By default equals SecurityType.CRYPTO.
    point_value:
        size of the contract as given by the ticker's Data Provider. Used mostly by tickers of security_type FUTURE and
        by default equals 1.
    """
    def __init__(self, currency: str, quote_ccy: str, security_type: SecurityType = SecurityType.CRYPTO,
                 point_value: int = 1, rounding_precision: int = 5):
        ticker_str = currency + quote_ccy if currency != quote_ccy and quote_ccy is not None else currency
        super().__init__(ticker_str, security_type, point_value)
        self._currency = currency
        self._quote_ccy = quote_ccy
        self._rounding_precision = rounding_precision

    @classmethod
    def from_string(self, ticker_str: Union[str, Sequence[str]]) -> Union['Ticker', Sequence['Ticker']]:
        raise NotImplementedError('Binance from_string method is not implemented. Please use init function.')

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def quote_ccy(self) -> str:
        return self._quote_ccy

    @property
    def rounding_precision(self) -> int:
        return self._rounding_precision


class HaverTicker(Ticker):
    """Haver tickers representation. For example E025RE@EUSRVYS -> ticker: E025RE, EUSRVYS: database_name

    Parameters
    ------------
    ticker: str
        string containing series ID within a specific database
    database_name: str
        name of the database where the series is located
    security_type: SecurityType
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc. By default equals SecurityType.STOCK.
    point_value: int
        size of the contract as given by the ticker's Data Provider. Used mostly by tickers of security_type FUTURE and
        by default equals 1.
    """
    def __init__(self, ticker: str, database_name: str, security_type: SecurityType = SecurityType.STOCK,
                 point_value: int = 1):
        super().__init__(ticker, security_type, point_value)
        self.database_name = database_name

    def as_string(self) -> str:
        """
        returns a string that can be used by the official Haver API to get the series
        """
        return self.ticker + '@' + self.database_name

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.STOCK,
                    point_value: int = 1) -> Union["HaverTicker", Sequence["HaverTicker"]]:
        """ Example: HaverTicker.from_string('RECESSQ2@USECON') """

        def to_ticker(ticker_string: str):
            ticker, db_name = ticker_string.split('@')
            return HaverTicker(ticker, db_name, security_type=security_type, point_value=point_value)

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]


class QuandlTicker(Ticker):
    """ Representation of Quandl tickers.

    Parameters
    ------------
    ticker: str
        string containing series ID within a specific database
    database_name: str
        name of the database where the series is located
    database_type: QuandlDBType
        type of the database
    security_type: SecurityType
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc. By default equals SecurityType.STOCK.
    point_value: int
        size of the contract as given by the ticker's Data Provider. Used mostly by tickers of security_type FUTURE and
        by default equals 1.
    """
    def __init__(self, ticker: str, database_name: str, database_type: QuandlDBType = QuandlDBType.Timeseries,
                 security_type: SecurityType = SecurityType.STOCK, point_value: int = 1):
        super().__init__(ticker, security_type, point_value)
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
    def from_string(cls, ticker_str: Union[str, Sequence[str]], db_type: QuandlDBType = QuandlDBType.Timeseries,
                    security_type: SecurityType = SecurityType.STOCK, point_value: int = 1) \
            -> Union["QuandlTicker", Sequence["QuandlTicker"]]:
        """
        Example: QuandlTicker.from_string('WIKI/MSFT')
        Note: this method supports only the Timeseries tickers at the moment.
        """

        def to_ticker(ticker_string: str):
            db_name, ticker = ticker_string.rsplit('/', 1)
            return QuandlTicker(ticker, db_name, db_type, security_type=security_type, point_value=point_value)

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]


class CcyTicker(Ticker):
    """ Representation of Cryptocurrency tickers.

    Parameters
    ------------
    ticker: str
        The name of the crypto currency. For example Bitcoin -> ticker: bitcoin
    security_type: SecurityType
        denotes the type of the security, that the ticker is representing e.g. SecurityType.STOCK for a stock,
        SecurityType.FUTURE for a futures contract etc. By default equals SecurityType.CRYPTO.
    point_value: int
        size of the contract as given by the ticker's Data Provider. Used mostly by tickers of security_type FUTURE and
        by default equals 1.
    """
    def __init__(self, ticker: str, security_type: SecurityType = SecurityType.CRYPTO, point_value: int = 1):
        super().__init__(ticker, security_type, point_value)

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.CRYPTO,
                    point_value: int = 1) -> Union["CcyTicker", Sequence["CcyTicker"]]:
        """ Example: CcyTicker.from_string('Bitcoin'). """

        def to_ticker(ticker_string: str,):
            return CcyTicker(ticker_string.lower(), security_type, point_value)

        if isinstance(ticker_str, str):
            return to_ticker(ticker_str)
        else:
            return [to_ticker(t) for t in ticker_str]
