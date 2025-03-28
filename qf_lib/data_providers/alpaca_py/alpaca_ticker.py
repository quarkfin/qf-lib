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

from typing import Union, Sequence, Optional

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker


class AlpacaTicker(Ticker):
    def __init__(self, ticker: str, security_type: SecurityType = SecurityType.STOCK,
                 point_value: int = 1, currency: Optional[str] = None):
        super().__init__(ticker, security_type, point_value, currency)

    @classmethod
    def from_string(self, ticker_str: Union[str, Sequence[str]]) -> Union['Ticker', Sequence['Ticker']]:
        if isinstance(ticker_str, str):
            return AlpacaTicker(ticker_str)
        else:
            return [AlpacaTicker(t) for t in ticker_str]
