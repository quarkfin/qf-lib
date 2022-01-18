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
from typing import Sequence, Union

from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker


class DummyTicker(Ticker):
    def __init__(self, ticker: str):
        super().__init__(ticker, SecurityType.STOCK, 1)

    @classmethod
    def from_string(cls, ticker_str: Union[str, Sequence[str]]) -> Union["DummyTicker", Sequence["DummyTicker"]]:
        """ Example: DummyTicker.from_string('AAA') """
        return DummyTicker(ticker_str) if isinstance(ticker_str, str) else [DummyTicker(t) for t in ticker_str]
