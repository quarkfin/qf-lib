from datetime import datetime

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class Transaction(object):
    """
    Encapsulates the notion of a filled Order, as returned from a Brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores the commission of the trade from the Brokerage.
    """

    def __init__(self, time: datetime, contract: Contract, quantity: int, price: float, commission: float):
        """
        Parameters
        ----------
        time
            time when the order was filled
        contract
            contract identifying the asset
        quantity
            filled quantity, positive for assets bought and negative for assets sold
        price
            price at which the trade was filled
        commission
            brokerage commission for carrying out the trade
        """
        self.time = time
        self.contract = contract
        self.quantity = quantity
        self.price = price
        self.commission = commission

    def average_price_including_commission(self) -> float:
        """
        Returns average price that we obtain by selling asset or the average price that we paid to buy asset.
        It always includes the commission paid.
        """
        result = self.quantity * self.price
        result += self.commission
        result /= self.quantity
        return result

    def __str__(self):
        string_template = "{datetime_str:s} - {class_name:<25} -> Contract: {contract_str:>30}," \
                          "Quantity: {quantity:>7}, Price: {price:>7.2f}, " \
                          "Commission: {commission:>7.2f}".\
            format(
                datetime_str=date_to_str(self.time), class_name=self.__class__.__name__,
                contract_str=str(self.contract), quantity=self.quantity, price=self.price,
                commission=self.commission
            )

        return string_template

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Transaction):
            return False

        return (self.time, self.contract, self.quantity, self.price, self.commission) == \
               (other.time, other.contract, other.quantity, other.price, other.commission)
