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

from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date

time = str_to_date("2010-01-01")
ticker = BloombergTicker("MSFT US Equity", security_type=SecurityType.STOCK)
quantity = 13
price = 100.5
commission = 1.2


def main():
    transaction = Transaction(time, ticker, quantity, price, commission)
    print(transaction)


if __name__ == '__main__':
    main()
