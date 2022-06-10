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
import decimal


class OrderRounder:
    """
    This is only used when trading crypto assets
    In practice crypto exchanges expect the order quantity to be rounded to certain precision.
    This class provides that functionality - with round_down method
    Rounding should not be used in Backtesting and BacktestTradingSession as rounding will prevent closing the
    position completely (there will be tiny position due to rounding) therefore the trades will not be calculated correctly
    """
    _is_rounding_on = True

    @classmethod
    def round_down(cls, value, rounding_precision):
        if not cls._is_rounding_on:
            return value

        value_type = type(value)
        with decimal.localcontext() as ctx:
            d = decimal.Decimal(value)
            ctx.rounding = decimal.ROUND_DOWN
            return value_type(round(d, rounding_precision))

    @classmethod
    def switch_off_rounding_for_backtest(cls):
        cls._is_rounding_on = False

    @classmethod
    def set_rounding_mode(cls, is_rounding_on: bool):
        cls._is_rounding_on = is_rounding_on
