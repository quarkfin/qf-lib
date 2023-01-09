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
from threading import Event
from typing import List
from math import isclose

from ibapi.client import OrderId, TickerId
from ibapi.contract import Contract
from ibapi.order import Order as IBOrder
from ibapi.order_state import OrderState
from ibapi.utils import iswrapper, current_fn_name
from ibapi.wrapper import EWrapper

from qf_lib.backtesting.contract.contract_to_ticker_conversion.ib_contract_ticker_mapper import IBContractTickerMapper
from qf_lib.backtesting.order.execution_style import StopOrder, MarketOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.broker_positon import BrokerPosition
from qf_lib.common.utils.logging.qf_parent_logger import ib_logger
from qf_lib.common.utils.miscellaneous.constants import ISCLOSE_REL_TOL, ISCLOSE_ABS_TOL
from qf_lib.brokers.ib_broker.ib_contract import IBContract


class IBWrapper(EWrapper):
    def __init__(self, action_event_lock: Event, contract_ticker_mapper: IBContractTickerMapper):
        super().__init__()
        self.action_event_lock = action_event_lock
        self.logger = ib_logger.getChild(self.__class__.__name__)
        self.contract_ticker_mapper = contract_ticker_mapper

        self.net_liquidation = None
        self.tmp_value = None
        self.nextValidOrderId = None
        self.position_list = []  # type: List[BrokerPosition]
        self.order_list = []  # type: List[Order]
        self.historical_data = {}
        self.contract_details = None
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
    def contractDetails(self, reqId, contractDetails):
        super(IBWrapper, self).contractDetails(reqId, contractDetails)
        self.contract_details = contractDetails

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
    def position(self, account: str, ib_contract: Contract, position: float, avgCost: float):
        """
        Important note: For futures, the exchange field will not be populated in the position callback as some futures
        trade on multiple exchanges.
        """
        if not position.is_integer():
            self.logger.warning(f"Position {ib_contract} has non-integer quantity = {position}")

        if not isclose(position, 0, rel_tol=ISCLOSE_REL_TOL, abs_tol=ISCLOSE_ABS_TOL):
            try:
                ticker = self.contract_ticker_mapper.contract_to_ticker(IBContract.from_ib_contract(ib_contract))
                position_info = BrokerPosition(ticker, position, avgCost)
                self.position_list.append(position_info)
            except ValueError as e:
                self.logger.error(f"Position for contract {ib_contract} will be skipped due to the following error "
                                  f"during parsing: \n{e}")

    @iswrapper
    def positionEnd(self):
        self.action_event_lock.set()

    @iswrapper
    def historicalData(self, reqId: int, bar):
        if reqId in self.historical_data:
            self.historical_data[reqId]['Dates'].append(bar.date)
            self.historical_data[reqId]['Open'].append(bar.open)
            self.historical_data[reqId]['High'].append(bar.high)
            self.historical_data[reqId]['Low'].append(bar.low)
            self.historical_data[reqId]['Close'].append(bar.close)
            self.historical_data[reqId]['Volume'].append(bar.volume)
        else:
            self.historical_data[reqId] = {'Dates': [bar.date], 'Open': [bar.open], 'High': [bar.high], 'Low': [bar.low],
                                           'Close': [bar.close], 'Volume': [bar.volume]}

    @iswrapper
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        self.action_event_lock.set()

    @iswrapper
    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float,
                    permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        self.logAnswer(current_fn_name(), vars())

        if self._order_id_awaiting_submit == orderId and status in ['PreSubmitted', 'Submitted', 'PendingSubmit']:
            self.logger.info('===> Order ID: {}, status: {}'.format(orderId, status))
            self.action_event_lock.set()

        if self._order_id_awaiting_cancel == orderId and status == 'Cancelled':
            self.logger.info('===> Order ID: {}, status: {}'.format(orderId, status))
            self.action_event_lock.set()

    @iswrapper
    def openOrder(self, orderId: OrderId, ib_contract: Contract, ib_order: IBOrder, orderState: OrderState):
        super().openOrder(orderId, ib_contract, ib_order, orderState)

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

        try:
            ticker = self.contract_ticker_mapper.contract_to_ticker(IBContract.from_ib_contract(ib_contract))
            order = Order(ticker=ticker, quantity=quantity, execution_style=execution_style,
                          time_in_force=time_in_force, order_state=orderState.status)

            order.id = int(orderId)
            self.order_list.append(order)
        except ValueError as e:
            self.logger.error(f"Open Order for contract {ib_contract} will be skipped due to the following error "
                              f"during parsing: \n{e}")

    @iswrapper
    def openOrderEnd(self):
        self.action_event_lock.set()

    @iswrapper
    def execDetails(self, reqId: int, contract: IBContract, execution):
        super().execDetails(reqId, contract, execution)
        self.logger.info(f"ExecDetails. ReqId: {reqId}, Symbol: {contract.symbol}, SecType: {contract.secType}, "
                         f"Currency: {contract.currency}, execution")

    @iswrapper
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        self.action_event_lock.set()

    @iswrapper
    def commissionReport(self, commissionReport):
        super().commissionReport(commissionReport)
        self.logger.info(f"CommissionReport: {commissionReport}")

    @iswrapper
    def contractDetailsEnd(self, reqId: int):
        self.action_event_lock.set()

    def next_order_id(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    def reset_position_list(self):
        self.position_list = []

    def reset_order_list(self):
        self.order_list = []

    def reset_historical_data(self):
        self.historical_data = {}

    def set_waiting_order_id(self, order_id: int):
        self._order_id_awaiting_submit = order_id

    def set_cancel_order_id(self, order_id):
        self._order_id_awaiting_cancel = order_id

    def reset_contract_details(self):
        self.contract_details = None

    def set_contract_details(self, contract_details):
        self.contract_details = contract_details
