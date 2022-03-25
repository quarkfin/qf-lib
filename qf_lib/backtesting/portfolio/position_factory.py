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
from qf_lib.backtesting.portfolio.backtest_crypto_position import BacktestCryptoPosition
from qf_lib.backtesting.portfolio.backtest_equity_position import BacktestEquityPosition
from qf_lib.backtesting.portfolio.backtest_future_position import BacktestFuturePosition
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import Ticker


class BacktestPositionFactory:
    @staticmethod
    def create_position(ticker: Ticker) -> BacktestPosition:
        """
        Creates a backtest position according to the asset class (security_type) of the security
        as defined in the Contract
        """
        sec_type = ticker.security_type
        if sec_type == SecurityType.STOCK:
            return BacktestEquityPosition(ticker)
        elif sec_type == SecurityType.FUTURE:
            return BacktestFuturePosition(ticker)
        elif sec_type == SecurityType.CRYPTO:
            return BacktestCryptoPosition(ticker)
        else:
            raise ValueError("Ticker security type: '{}' is not currently supported.")
