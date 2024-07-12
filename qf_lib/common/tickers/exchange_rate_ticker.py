from typing import Optional, Sequence, Union
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker


class CurrencyExchangeTicker(Ticker):
    """Ticker representing a foreign exchange rate from one ticker to another.

    Parameters
    ----------
    ticker: str
        identifier of the security in a specific database.
    from_currency: str
        The ISO code of the from currency in the exchange rate.
    to_currency: str
        The ISO code of the to currency in the exchange rate.
    point_value: int
        Used to define the size of the contract.
    security_type: SecurityType
        Enum which denotes the type of the security.

    """
    def __init__(self, ticker: str, from_currency: str, to_currency: str, point_value: int = 1,
                 security_type: SecurityType = SecurityType.FX):
        super().__init__(ticker, security_type, point_value, to_currency)
        self.from_currency = from_currency
        self.to_currency = to_currency

    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.FX,
                    point_value: int = 1, currency: Optional[str] = None
                    ) -> Union["CurrencyExchangeTicker", Sequence["CurrencyExchangeTicker"]]:
        if isinstance(ticker_str, str):
            return CurrencyExchangeTicker(ticker_str, security_type, point_value, currency)


class BloombergCurrencyExchangeTicker(BloombergTicker):
    """BloombergTicker representing a foreign exchange rate from one ticker to another.

    Parameters
    ----------
    ticker: str
        identifier of the security in a specific database.
    from_currency: str
        The ISO code of the from currency in the exchange rate.
    to_currency: str
        The ISO code of the to currency in the exchange rate.
    point_value: int
        Used to define the size of the contract.
    security_type: SecurityType
        Enum which denotes the type of the security.

    """
    def __init__(self, ticker: str, from_currency: str, to_currency: str, point_value: int = 1,
                 security_type: SecurityType = SecurityType.FX):
        super().__init__(ticker, security_type, point_value, to_currency)
        self.from_currency = from_currency
        self.to_currency = to_currency

    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.FX,
                    point_value: int = 1, currency: Optional[str] = None
                    ) -> Union["CurrencyExchangeTicker", Sequence["CurrencyExchangeTicker"]]:
        if isinstance(ticker_str, str):
            return CurrencyExchangeTicker(ticker_str, security_type, point_value, currency)
