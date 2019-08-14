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

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.position import Position


class BrokerPosition(Position):
    def __init__(self, contract: Contract, position: float, avg_cost: float):
        self._contract = contract
        self._quantity = position
        self._avg_cost = avg_cost

    def contract(self) -> Contract:
        return self._contract

    def quantity(self) -> float:
        return self._quantity

    def avg_cost_per_share(self) -> float:
        return self._avg_cost

    def __str__(self):
        return 'BrokerPosition:\n' \
               '\tcontract: {}\n' \
               '\tquantity: {}\n' \
               '\tavg cost per share: {}\n'.format(str(self.contract()), self.quantity(), self.avg_cost_per_share())
