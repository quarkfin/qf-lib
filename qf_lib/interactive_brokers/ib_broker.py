import logging
from threading import Thread, Event, Lock
from typing import List, Optional

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order

from qf_lib.interactive_brokers.ib_utils import IBPositionInfo, IBOrderInfo
from qf_lib.interactive_brokers.ib_wrapper import IBWrapper


class IBBroker(object):
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

    def get_portfolio_value(self) -> Optional[float]:
        with self.lock:
            request_id = 1
            self.client.reqAccountSummary(request_id, 'All', 'NetLiquidation')
            wait_result = self._wait_for_results()
            self.client.cancelAccountSummary(request_id)

            if wait_result:
                return self.wrapper.net_liquidation
            else:
                self.logger.error('===> Time out while getting portfolio value')
                return None

    def get_portfolio_tag(self, tag: str) -> Optional[float]:
        with self.lock:
            request_id = 2
            self.client.reqAccountSummary(request_id, 'All', tag)
            wait_result = self._wait_for_results()
            self.client.cancelAccountSummary(request_id)

            if wait_result:
                return self.wrapper.tmp_value
            else:
                self.logger.error('===> Time out while getting portfolio tag: {}'.format(tag))
                return None

    def get_positions(self) -> Optional[List[IBPositionInfo]]:
        with self.lock:
            self.wrapper.reset_position_list()
            self.client.reqPositions()

            if self._wait_for_results():
                return self.wrapper.position_list
            else:
                self.logger.error('===> Time out while getting positions')
                return None

    def place_order(self, contract: Contract, order: Order) -> Optional[int]:
        with self.lock:
            order_id = self.wrapper.next_order_id()
            self.wrapper.set_waiting_order_id(order_id)
            self.client.placeOrder(order_id, contract, order)

            if self._wait_for_results():
                return order_id
            else:
                self.logger.error('===> Time out while placing the trade for: \n'
                                  '\tcontract: {}\n'
                                  '\torder: {}'.format(contract, order))
                return None

    def cancel_order(self, order_id: int) -> bool:
        with self.lock:
            self.wrapper.set_cancel_order_id(order_id)
            self.client.cancelOrder(order_id)
            if self._wait_for_results():
                return True
            else:
                self.logger.error('===> Time out while cancelling order id {} : \n'.format(order_id))
                return False

    def get_open_orders(self)-> Optional[List[IBOrderInfo]]:
        with self.lock:
            self.wrapper.reset_order_list()
            self.client.reqOpenOrders()

            if self._wait_for_results():
                return self.wrapper.order_list
            else:
                self.logger.error('===> Time out while getting orders')
                return None

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
