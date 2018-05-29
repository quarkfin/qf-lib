from abc import ABCMeta, abstractmethod
from typing import Optional

from ibapi.client import OrderId
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.order_state import OrderState

from qf_lib.common.tickers.tickers import Ticker


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


class AbstractPosition(metaclass=ABCMeta):
    @abstractmethod
    def ticker(self) ->Ticker:
        pass

    @abstractmethod
    def quantity(self) -> float:
        pass

    @abstractmethod
    def avg_cost_per_share(self) -> float:
        pass


class IBPositionInfo(AbstractPosition):
    def __init__(self, contract: Contract, position: float, avg_cost: float):
        self.contract = contract
        self._quantity = position  # quantity
        self.avg_cost = avg_cost

    def ticker(self) -> Optional[Ticker]:
        raise NotImplementedError()

    def quantity(self) -> float:
        return self._quantity

    def avg_cost_per_share(self) -> float:
        return self.avg_cost

    def __str__(self):
        return 'Position Info:\n' \
               '\tticker: {}\n' \
               '\tcontract: {}\n' \
               '\tquantity: {}\n' \
               '\tavg cost: {}\n'.format(self.ticker(), self.contract, self._quantity, self.avg_cost)


class IBOrderInfo(object):
    def __init__(self, order_id: OrderId, contract: Contract, order: Order, order_state: OrderState):
        self.order_id = order_id
        self.contract = contract
        self.order = order
        self.orderState = order_state

    def __str__(self):
        return 'Order Info:\n' \
               '\torderId: {}\n' \
               '\tcontract: {}\n' \
               '\torder: {}\n' \
               '\torderState: {}\n'.format(self.order_id, self.contract, self.order, self.orderState)
