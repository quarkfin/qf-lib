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
import copy
from typing import Tuple, Optional
from numpy import sign

from qf_lib.backtesting.portfolio.transaction import Transaction


def split_transaction_if_needed(existing_quantity: float, transaction: Transaction) \
            -> Tuple[bool, Transaction, Optional[Transaction]]:
    """
    Splits the given transaction into two if needed. The split occurs, in case if the transaction would result in the
    change of existing position direction, e.g. assuming there exist 200 shares of a certain contract in the portfolio,
    a Transaction of quantity = -500, should be divided into:
    - closing Transaction with the quantity = -200
    - remaining Transaction with the quantity = -300
    Commissions are adjusted proportionally.

    Parameters
    -----------
    existing_quantity: float
        Number of shares of the given contract, already existing in the portfolio
    transaction: Transaction
        transaction that eventually needs to be split

    Returns
    --------
    Tuple[bool, Transaction, Optional[Transaction]]
        boolean indicating whether the split was performed (True) or not (False) and the transaction (transactions)
    """

    sign_before = sign(existing_quantity)
    sign_after = sign(existing_quantity + transaction.quantity)

    if sign_before * sign_after == -1:
        closing_quantity = -existing_quantity
        closing_transaction = copy.deepcopy(transaction)
        closing_transaction.quantity = closing_quantity
        closing_transaction.commission = transaction.commission * (closing_quantity / transaction.quantity)

        remaining_quantity = transaction.quantity - closing_quantity
        remaining_transaction = copy.deepcopy(transaction)
        remaining_transaction.quantity = remaining_quantity
        remaining_transaction.commission = transaction.commission * (remaining_quantity / transaction.quantity)
        return True, closing_transaction, remaining_transaction

    return False, transaction, None
