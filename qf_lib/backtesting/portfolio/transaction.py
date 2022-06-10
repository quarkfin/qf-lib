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

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class Transaction:
    """
    Encapsulates the notion of a filled Order, as returned from a Brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores the commission of the trade from the Brokerage.
    Parameters
    ----------
    transaction_fill_time: datetime
        time when the order was filled
    ticker: Ticker
        ticker identifying the asset
    quantity: float
        filled quantity, positive for assets bought and negative for assets sold
    price: float
        price at which the trade was filled
    commission: float
        brokerage commission for carrying out the trade. It is always a positive number
    """

    def __init__(self, transaction_fill_time: datetime, ticker: Ticker, quantity: float, price: float,
                 commission: float, trade_id=None, account=None, strategy=None, broker=None, currency=None):

        assert commission >= 0.0

        self.transaction_fill_time = transaction_fill_time
        self.ticker = ticker
        self.quantity = quantity
        self.price = price
        self.commission = commission

        # additional fields
        self.net_amount = quantity * price - commission
        self.trade_id = trade_id
        self.account = account
        self.strategy = strategy
        self.broker = broker
        self.currency = currency

    @staticmethod
    def get_header():
        return ["Transaction_fill_time", "Asset_name", "Contract_symbol", "Security_type", "Contract_size", "Quantity",
                "Price", "Commission", "Net_amount", "Trade_ID", "Account", "Strategy", "Broker", "Currency"]

    def get_row(self):
        row = [self.transaction_fill_time,
               self.ticker.name,
               self.ticker.ticker,
               self.ticker.security_type.value,
               self.ticker.point_value,
               self.quantity,
               self.price,
               self.commission,
               self.net_amount,
               self.trade_id,
               self.account,
               self.strategy,
               self.broker,
               self.currency]
        return row

    def __str__(self):
        return f"{self.__class__.__name__} ({date_to_str(self.transaction_fill_time)}) -> " \
               f"Quantity: {self.quantity:>8}, " \
               f"Price: {self.price:>10.2f}, " \
               f"Commission: {self.commission:>12.8f}, " \
               f"Net Amount: {self.net_amount:>20.8f}, " \
               f"Ticker: {self.ticker}, " \
               f"Trade_id: {self.trade_id}, " \
               f"Account: {self.account}, " \
               f"Strategy: {self.strategy}, " \
               f"Broker: {self.broker}, " \
               f"Currency: {self.currency}"

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Transaction):
            return False

        return (self.transaction_fill_time, self.ticker, self.quantity, self.price, self.commission) == \
               (other.transaction_fill_time, other.ticker, other.quantity, other.price, other.commission)
