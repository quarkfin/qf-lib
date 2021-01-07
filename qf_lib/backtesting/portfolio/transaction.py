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

from datetime import datetime

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class Transaction(object):
    """
    Encapsulates the notion of a filled Order, as returned from a Brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores the commission of the trade from the Brokerage.

    Parameters
    ----------
    time: datetime
        time when the order was filled
    contract: Contract
        contract identifying the asset
    quantity: int
        filled quantity, positive for assets bought and negative for assets sold
    price: float
        price at which the trade was filled
    commission: float
        brokerage commission for carrying out the trade. It is always a positive number
    """

    def __init__(self, time: datetime, contract: Contract, quantity: int, price: float, commission: float):
        assert commission >= 0.0

        self.time = time
        self.contract = contract
        self.quantity = quantity
        self.price = price
        self.commission = commission

    def __str__(self):
        string_template = "{class_name:s} ({datetime_str:s}) -> " \
                          "Quantity: {quantity:>8}, " \
                          "Price: {price:>10.2f}, " \
                          "Commission: {commission:>7.2f}, " \
                          "Contract: {contract_str:}".format(class_name=self.__class__.__name__,
                                                             datetime_str=date_to_str(self.time),
                                                             quantity=self.quantity,
                                                             price=self.price,
                                                             commission=self.commission,
                                                             contract_str=str(self.contract)
                                                             )

        return string_template

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Transaction):
            return False

        return (self.time, self.contract, self.quantity, self.price, self.commission) == \
               (other.time, other.contract, other.quantity, other.price, other.commission)
