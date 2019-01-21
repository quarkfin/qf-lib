from threading import Thread, Event, Lock
from typing import List, Sequence

from ibapi.client import EClient
from ibapi.contract import Contract as IBContract
from ibapi.order import Order as IBOrder

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.common.exceptions.broker_exceptions import BrokerException, OrderCancellingException
from qf_lib.common.utils.logging.qf_parent_logger import ib_logger
from qf_lib.interactive_brokers.ib_wrapper import IBWrapper
from qf_lib.backtesting.contract.contract import Contract


class IBBroker(Broker):
    def __init__(self):
        self.logger = ib_logger.getChild(self.__class__.__name__)
        self.lock = Lock()
        self.waiting_time = 60  # expressed in seconds
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
            self._reset_action_lock()
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
            self._reset_action_lock()
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
            self._reset_action_lock()
            self.wrapper.reset_position_list()
            self.client.reqPositions()

            if self._wait_for_results():
                return self.wrapper.position_list
            else:
                error_msg = 'Time out while getting positions'
                self.logger.error('===> {}'.format(error_msg))
                raise BrokerException(error_msg)

    def place_orders(self, orders: Sequence[Order]) -> Sequence[int]:
        order_ids_list = []
        for order in orders:
            self.logger.info('Placing Order: {}'.format(order))
            order_id = self._execute_single_order(order)
            order_ids_list.append(order_id)

        return order_ids_list

    def cancel_order(self, order_id: int):
        with self.lock:
            self.logger.info('cancel_order: {}'.format(order_id))
            self._reset_action_lock()
            self.wrapper.set_cancel_order_id(order_id)
            self.client.cancelOrder(order_id)

            if not self._wait_for_results():
                error_msg = 'Time out while cancelling order id {} : \n'.format(order_id)
                self.logger.error('===> {}'.format(error_msg))
                raise OrderCancellingException(error_msg)

    def get_open_orders(self) -> List[Order]:
        with self.lock:
            self._reset_action_lock()
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
            self.logger.info('cancel_all_open_orders')

    def _execute_single_order(self, order) -> int:
        with self.lock:
            order_id = self.wrapper.next_order_id()

            self._reset_action_lock()
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

    def _wait_for_results(self) -> bool:
        """ Wait for self.waiting_time """
        wait_result = self.action_event_lock.wait(self.waiting_time)
        return wait_result

    def _reset_action_lock(self):
        """ threads calling wait() will block until set() is called"""
        self.action_event_lock.clear()

    def _to_ib_contract(self, contract: Contract):
        ib_contract = IBContract()
        ib_contract.symbol = contract.symbol
        ib_contract.secType = contract.security_type
        ib_contract.exchange = contract.exchange
        return ib_contract

    def _to_ib_order(self, order: Order):
        ib_order = IBOrder()

        if order.quantity > 0:
            ib_order.action = 'BUY'
        else:
            ib_order.action = 'SELL'

        ib_order.totalQuantity = abs(order.quantity)

        execution_style = order.execution_style
        self._set_execution_style(ib_order, execution_style)

        time_in_force = order.time_in_force
        tif_str = self._map_to_tif_str(time_in_force)
        ib_order.tif = tif_str

        return ib_order

    def _map_to_tif_str(self, time_in_force):
        if time_in_force == TimeInForce.GTC:
            tif_str = "GTC"
        elif time_in_force == TimeInForce.DAY:
            tif_str = "DAY"
        elif time_in_force == TimeInForce.OPG:
            tif_str = "OPG"
        else:
            raise ValueError("Not supported TimeInForce {tif:s}".format(tif=str(time_in_force)))

        return tif_str

    def _set_execution_style(self, ib_order, execution_style):
        if isinstance(execution_style, MarketOrder):
            ib_order.orderType = "MKT"
        elif isinstance(execution_style, StopOrder):
            ib_order.orderType = "STP"
            ib_order.auxPrice = execution_style.stop_price
