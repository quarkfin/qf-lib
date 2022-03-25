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

from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel


class IBCommissionModel(CommissionModel):
    """
    Interactive Brokers commission for a transaction.

    This is based on the US Fixed pricing, the details of which can be found here:
    https://www.interactivebrokers.co.uk/en/index.php?f=1590&p=stocks1
    """

    def calculate_commission(self, fill_quantity: float, fill_price: float) -> float:
        fill_quantity = abs(fill_quantity)
        commission = max(1.0, min(0.005 * fill_quantity, 0.01 * fill_price * fill_quantity))

        return commission
