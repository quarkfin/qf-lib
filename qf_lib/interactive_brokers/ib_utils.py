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

from ibapi.contract import Contract
from ibapi.order import Order


def wse_stock(symbol: str):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "WSE"
    return contract


def nyse_stock(symbol: str):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "NYSE"
    return contract


def market_order(action: str, quantity: float):
    order = Order()
    order.action = action
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order


def stop_order(action: str, quantity: float, stop_price: float):
    order = Order()
    order.action = action
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.tif = "GTC"
    order.auxPrice = stop_price
    return order
