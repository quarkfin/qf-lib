import logging
from threading import Thread, Event, Lock
from typing import List

from ibapi.client import EClient
from ibapi.contract import Contract as IBContract
from ibapi.order import Order as IBOrder

from qf_lib.backtesting.qstrader.broker.broker import Broker
from qf_lib.backtesting.qstrader.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.backtesting.qstrader.portfolio.position import Position
from qf_lib.common.exceptions.broker_exceptions import BrokerException, OrderCancellingException
from qf_lib.interactive_brokers.ib_wrapper import IBWrapper


class IBBroker(Broker):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.lock = Lock()
        self.waiting_time = 5  # expressed in seconds
        self.action_event_lock = Event()
        self.wrapper = IBWrapper(self.action_event_lock)
        self.client = EClient(wrapper=self.wrapper)
        self.client.connect("127.0.0.1", 7497, clientId=0)

        # run the client in the separate thread so that the execution of the program can go on
        # now we will have 3 threads:
        # - thread of the main program
        # - thread of the client
        # - thread of the wrapper
        thread = Thread(target=self.client.run)
        thread.start()
        # this will be released after the client initialises and wrapper receives the nextValidOrderId
        if not self._wait_for_results():
            raise ConnectionError("IB Broker was not initialized correctly")

    def get_portfolio_value(self) -> float:
        with self.lock:
            request_id = 1
            self.client.reqAccountSummary(request_id, 'All', 'NetLiquidation')
            wait_result = self._wait_for_results()
            self.client.cancelAccountSummary(request_id)

            if wait_result:
                return self.wrapper.net_liquidation
            else:
                error_msg = 'Time out while getting portfolio value'
                self.logger.error('===> {}'.format(error_msg))
                raise BrokerException(error_msg)

    def get_portfolio_tag(self, tag: str) -> float:
        with self.lock:
            request_id = 2
            self.client.reqAccountSummary(request_id, 'All', tag)
            wait_result = self._wait_for_results()
            self.client.cancelAccountSummary(request_id)

            if wait_result:
                return self.wrapper.tmp_value
            else:
                error_msg = 'Time out while getting portfolio tag: {}'.format(tag)
                self.logger.error('===> {}'.format(error_msg))
                raise BrokerException(error_msg)

    def get_positions(self) -> List[Position]:
        with self.lock:
            self.wrapper.reset_position_list()
            self.client.reqPositions()

            if self._wait_for_results():
                return self.wrapper.position_list
            else:
                error_msg = 'Time out while getting positions'
                self.logger.error('===> {}'.format(error_msg))
                raise BrokerException(error_msg)

    def place_order(self, order: Order) -> int:
        with self.lock:
            order_id = self.wrapper.next_order_id()
            self.wrapper.set_waiting_order_id(order_id)

            ib_contract = self._to_ib_contract(order.contract)
            ib_order = self._to_ib_order(order)

            self.client.placeOrder(order_id, ib_contract, ib_order)

            if self._wait_for_results():
                return order_id
            else:
                error_msg = 'Time out while placing the trade for: \n\torder: {}'.format(order)
                self.logger.error('===> {}'.format(error_msg))
                raise BrokerException(error_msg)

    def cancel_order(self, order_id: int):
        with self.lock:
            self.wrapper.set_cancel_order_id(order_id)
            self.client.cancelOrder(order_id)

            if not self._wait_for_results():
                error_msg = 'Time out while cancelling order id {} : \n'.format(order_id)
                self.logger.error('===> {}'.format(error_msg))
                raise OrderCancellingException(error_msg)

    def get_open_orders(self)-> List[Order]:
        with self.lock:
            self.wrapper.reset_order_list()
            self.client.reqOpenOrders()

            if self._wait_for_results():
                return self.wrapper.order_list
            else:
                error_msg = 'Time out while getting orders'
                self.logger.error('===> {}'.format(error_msg))
                raise BrokerException(error_msg)

    def cancel_all_open_orders(self):
        """
        There is now way to check if cancelling of all orders was finished.
        One can only get open orders and confirm that the list is empty
        """
        with self.lock:
            self.client.reqGlobalCancel()

    def _wait_for_results(self) -> bool:
        wait_result = self.action_event_lock.wait(self.waiting_time)
        self.action_event_lock.clear()
        return wait_result

    def _to_ib_contract(self, contract):
        ib_contract = IBContract()
        ib_contract.symbol = contract.symbol
        ib_contract.secType = contract.security_type
        ib_contract.exchange = contract.exchange
        return ib_contract

    def _to_ib_order(self, order):
        ib_order = IBOrder()

        if order.quantity > 0:
            ib_order.action = 'BUY'
        else:
            ib_order.action = 'SELL'

        ib_order.totalQuantity = abs(order.quantity)

        execution_style = order.execution_style
        self._set_execution_style(ib_order, execution_style)

        ib_order.tif = order.tif
        return ib_order

    def _set_execution_style(self, ib_order, execution_style):
        if isinstance(execution_style, MarketOrder):
            ib_order.orderType = "MKT"
        elif isinstance(execution_style, StopOrder):
            ib_order.orderType = "STP"
            ib_order.auxPrice = execution_style.stop_price
