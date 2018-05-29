import logging
from threading import Event
from typing import List

from ibapi.client import OrderId, TickerId
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.utils import iswrapper, current_fn_name
from ibapi.wrapper import EWrapper

from qf_lib.interactive_brokers.ib_utils import IBPositionInfo, IBOrderInfo


class IBWrapper(EWrapper):
    def __init__(self, action_event_lock: Event):

        self.action_event_lock = action_event_lock
        self.logger = logging.getLogger(self.__class__.__name__)

        self.net_liquidation = None
        self.tmp_value = None
        self.nextValidOrderId = None
        self.position_list = []  # type:  List[IBPositionInfo]
        self.order_list = []  # type:  List[IBOrderInfo]
        self._order_id_awaiting_submit = None  # type:  int
        self._order_id_awaiting_cancel = None  # type:  int

    @iswrapper
    def logAnswer(self, fn_name, fn_params):
        if 'self' in fn_params:
            params_dict = dict(fn_params)
            del params_dict['self']
        else:
            params_dict = fn_params
            self.logger.info("->Function Call: \n"  
                             "\tFunction Name: {}\n"
                             "\tParameters:".format(fn_name))
        for k, v in params_dict.items():
            self.logger.info("\t\t{}: {}".format(k, v))

    @iswrapper
    def error(self, req_id: TickerId, error_code: int, error_string: str):
        if req_id == -1 and error_code != 502:
            self.logger.info("-> Data Connection info: {} {} {}".format(req_id, error_code, error_string))
        else:
            self.logger.error("===> ERROR {} {} {}".format(req_id, error_code, error_string))

    @iswrapper
    def nextValidId(self, orderId: int):
        self.nextValidOrderId = orderId
        self.logger.info("===> Next valid order ID: {}".format(orderId))
        self.action_event_lock.set()

    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        if tag == 'NetLiquidation':
            self.net_liquidation = float(value)
        else:
            self.tmp_value = float(value)

    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        self.action_event_lock.set()

    @iswrapper
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        position_info = IBPositionInfo(contract, position, avgCost)
        self.position_list.append(position_info)

    @iswrapper
    def positionEnd(self):
        self.action_event_lock.set()

    @iswrapper
    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float,
                    permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        self.logAnswer(current_fn_name(), vars())

        if self._order_id_awaiting_submit == orderId and status in ['PreSubmitted', 'Submitted']:
            self.logger.info('===> Order ID: {}, status: {}'.format(orderId, status))
            self.action_event_lock.set()

        if self._order_id_awaiting_cancel == orderId and status == 'Cancelled':
            self.logger.info('===> Order ID: {}, status: {}'.format(orderId, status))
            self.action_event_lock.set()

    @iswrapper
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        order_info = IBOrderInfo(orderId, contract, order, orderState)
        self.order_list.append(order_info)

    @iswrapper
    def openOrderEnd(self):
        self.action_event_lock.set()

    def next_order_id(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    def reset_position_list(self):
        self.position_list = []

    def reset_order_list(self):
        self.order_list = []

    def set_waiting_order_id(self, order_id: int):
        self._order_id_awaiting_submit = order_id

    def set_cancel_order_id(self, order_id):
        self._order_id_awaiting_cancel = order_id
