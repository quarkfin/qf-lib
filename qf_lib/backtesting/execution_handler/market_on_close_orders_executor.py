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

from qf_lib.backtesting.execution_handler.market_orders_executor import MarketOrdersExecutor
from qf_lib.backtesting.order.execution_style import MarketOnCloseOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce


class MarketOnCloseOrdersExecutor(MarketOrdersExecutor):
    def _check_order_validity(self, order):
        assert order.time_in_force == TimeInForce.DAY, \
            "Only TimeInForce.DAY Time in Force is accepted by MarketOnCloseOrdersExecutor"
        assert order.execution_style == MarketOnCloseOrder(), \
            "Only MarketOnCloseOrder ExecutionStyle is supported by MarketOnCloseOrdersExecutor"
