from typing import Sequence, Union
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker


class CurrencyExchangeTicker(BloombergTicker):

    def __init__(self, ticker: str, from_currency: str, to_currency: str, point_value: int = 1, security_type: SecurityType = SecurityType.FX):
        super().__init__(ticker, security_type, point_value)
        self.from_currency = from_currency
        self.to_currency = to_currency

    def from_string(cls, ticker_str: Union[str, Sequence[str]], security_type: SecurityType = SecurityType.FX,
                    point_value: int = 1) -> Union["CurrencyExchangeTicker", Sequence["CurrencyExchangeTicker"]]:
        if isinstance(ticker_str, str):
            return CurrencyExchangeTicker(ticker_str, security_type, point_value)
