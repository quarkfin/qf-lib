from threading import Event
from typing import List

from ibapi.client import OrderId, TickerId
from ibapi.contract import Contract as IBContract
from ibapi.order import Order as IBOrder
from ibapi.order_state import OrderState
from ibapi.utils import iswrapper, current_fn_name
from ibapi.wrapper import EWrapper

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.order.execution_style import StopOrder, MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.broker_positon import BrokerPosition
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class IBWrapper(EWrapper):
    def __init__(self, action_event_lock: Event):

        self.action_event_lock = action_event_lock
        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.net_liquidation = None
        self.tmp_value = None
        self.nextValidOrderId = None
        self.position_list = []  # type: List[Position]
        self.order_list = []  # type: List[Order]
        self._order_id_awaiting_submit = None  # type: int
        self._order_id_awaiting_cancel = None  # type: int

    @iswrapper
    def logAnswer(self, fn_name, fn_params):
        params_dict = fn_params
        if 'self' in params_dict:
            del params_dict['self']

        log_message = " -> Function Call: {}\n\tParameters:\n".format(fn_name)
        for k, v in params_dict.items():
            log_message += "\t\t{}: {}\n".format(k, v)

        self.logger.info(log_message)

    @iswrapper
    def error(self, req_id: TickerId, error_code: int, error_string: str):
        if req_id == -1 and error_code != 502:
            self.logger.info("Data Connection info: {} {} {}".format(req_id, error_code, error_string))
        else:
            self.logAnswer(current_fn_name(), vars())

    @iswrapper
    def nextValidId(self, orderId: int):
        self.nextValidOrderId = orderId
        self.logger.info("===> Next valid order ID: {}".format(orderId))
        self.action_event_lock.set()

    @iswrapper
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        if tag == 'NetLiquidation':
            self.net_liquidation = float(value)
            self.logger.info("===> NetLiquidation: {}".format(float(value)))
        else:
            self.tmp_value = float(value)

    @iswrapper
    def accountSummaryEnd(self, reqId: int):
        self.action_event_lock.set()

    @iswrapper
    def position(self, account: str, ib_contract: IBContract, position: float, avgCost: float):
        contract = Contract(ib_contract.symbol, ib_contract.secType, ib_contract.exchange)

        if not position.is_integer():
            self.logger.warning("Position {} has non-integer quantity = {}".format(contract, position))

        position_info = BrokerPosition(contract, int(position), avgCost)
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
    def openOrder(self, orderId: OrderId, ib_contract: IBContract, ib_order: IBOrder, orderState: OrderState):
        contract = Contract(ib_contract.symbol, ib_contract.secType, ib_contract.exchange)

        if ib_order.orderType.upper() == 'STP':
            execution_style = StopOrder(ib_order.auxPrice)
        elif ib_order.orderType.upper() == 'MKT':
            execution_style = MarketOrder()
        else:
            error_message = "Order Type is not supported: {}".format(ib_order.orderType)
            self.logger.error(error_message)
            raise ValueError(error_message)

        if ib_order.action.upper() == 'SELL':
            quantity = -ib_order.totalQuantity
        elif ib_order.action.upper() == 'BUY':
            quantity = ib_order.totalQuantity
        else:
            error_message = "Order Action is not supported: {}".format(ib_order.action)
            self.logger.error(error_message)
            raise ValueError(error_message)

        if ib_order.tif.upper() == 'DAY':
            time_in_force = TimeInForce.DAY
        elif ib_order.tif.upper() == 'GTC':
            time_in_force = TimeInForce.GTC
        elif ib_order.tif.upper() == 'OPG':
            time_in_force = TimeInForce.OPG
        else:
            error_message = "Time in Force is not supported: {}".format(ib_order.tif)
            self.logger.error(error_message)
            raise ValueError(error_message)

        order = Order(contract=contract, quantity=quantity, execution_style=execution_style,
                      time_in_force=time_in_force, order_state=orderState.status)

        order.id = int(orderId)
        self.order_list.append(order)

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
