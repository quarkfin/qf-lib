from typing import Union, Sequence, Optional

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker


class YFinanceTicker(Ticker):
    def __init__(self, ticker: str, security_type: SecurityType = SecurityType.STOCK,
                 point_value: int = 1, currency: Optional[str] = None):
        super().__init__(ticker, security_type, point_value, currency)

    @classmethod
    def from_string(self, ticker_str: Union[str, Sequence[str]]) -> Union['Ticker', Sequence['Ticker']]:
        if isinstance(ticker_str, str):
            return YFinanceTicker(ticker_str)
        else:
            return [YFinanceTicker(t) for t in ticker_str]
