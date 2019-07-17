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
