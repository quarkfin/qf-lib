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


class BpsTradeValueCommissionModel(CommissionModel):
    """
    Commission model which uses fixed bps rate for trade value. For example always 2pbs of the $ value ot the trade.

    Parameters
    ----------
    commission
        commission expressed in a basis points. (e.g. 2.0 denotes 2 pbs of trade value).

    """

    def __init__(self, commission: float):
        self.commission = commission

    def calculate_commission(self, fill_quantity: float, fill_price: float) -> float:
        fill_quantity = abs(fill_quantity)
        commission = fill_price * fill_quantity * self.commission / 10000
        return commission
