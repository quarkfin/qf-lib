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
from threading import Thread, Event, Lock
from typing import List, Sequence, Optional, Set

from ibapi.client import EClient
from ibapi.contract import ContractDetails
from ibapi.order import Order as IBOrder
from pandas import to_datetime

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract_to_ticker_conversion.ib_contract_ticker_mapper import IBContractTickerMapper
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.broker_positon import BrokerPosition
from qf_lib.common.exceptions.broker_exceptions import BrokerException, OrderCancellingException
from qf_lib.common.utils.logging.qf_parent_logger import ib_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.brokers.ib_broker.ib_contract import IBContract
from qf_lib.brokers.ib_broker.ib_wrapper import IBWrapper


class IBBroker(Broker):
    """
    Interactive Brokers Broker class. Main purpose of this class is to connect to the API of IB broker and send
    the orders. It provides the functionality, which allows to retrieve a.o. the currently open positions and the
    value of the portfolio.

    Parameters
    -----------
    contract_ticker_mapper: IBContractTickerMapper
        mapper which provides the functionality that allows to map a ticker from any data provider
        (BloombergTicker, PortaraTicker etc.) onto the contract object from the Interactive Brokers API
    clientId: int
        id of the Broker client
    host: str
        IP address
    port: int
        socket port
    """
    def __init__(self, contract_ticker_mapper: IBContractTickerMapper, clientId: int = 0, host: str = "127.0.0.1",
                 port: int = 7497):
        super().__init__(contract_ticker_mapper)
        self.logger = ib_logger.getChild(self.__class__.__name__)
        # Lock that synchronizes entries into the functions and makes sure we have a synchronous communication
        # with the client
        self.lock = Lock()
        self.orders_placement_lock = Lock()
        self.waiting_time = 30  # expressed in seconds
        # Lock that informs us that wrapper received the response
        self.action_event_lock = Event()
        self.wrapper = IBWrapper(self.action_event_lock, contract_ticker_mapper)
        self.client = EClient(wrapper=self.wrapper)
        self.clientId = clientId
        self.client.connect(host, port, self.clientId)

        # Run the client in the separate thread so that the execution of the program can go on
        # now we will have 3 threads:
        # - thread of the main program
        # - thread of the client
        # - thread of the wrapper
        thread = Thread(target=self.client.run)
        thread.start()

        # This will be released after the client initialises and wrapper receives the nextValidOrderId
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
                self.logger.error(error_msg)
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
                self.logger.error(error_msg)
                raise BrokerException(error_msg)

    def get_positions(self) -> List[BrokerPosition]:
        with self.lock:
            self._reset_action_lock()
            self.wrapper.reset_position_list()
            self.client.reqPositions()

            if self._wait_for_results():
                return self.wrapper.position_list
            else:
                error_msg = 'Time out while getting positions'
                self.logger.error(error_msg)
                raise BrokerException(error_msg)

    def get_liquid_hours(self, contract: IBContract) -> QFDataFrame:
        """ Returns a QFDataFrame containing information about liquid hours of the given contract. """
        with self.lock:
            self._reset_action_lock()
            request_id = 3
            self.client.reqContractDetails(request_id, contract)

            if self._wait_for_results():
                contract_details = self.wrapper.contract_details
                liquid_hours = contract_details.tradingHours.split(";")
                liquid_hours_df = QFDataFrame.from_records(
                    [hours.split("-") for hours in liquid_hours if not hours.endswith("CLOSED")], columns=["FROM", "TO"]
                )
                for col in liquid_hours_df.columns:
                    liquid_hours_df[col] = to_datetime(liquid_hours_df[col], format="%Y%m%d:%H%M")

                liquid_hours_df.name = contract_details.contract.symbol
                return liquid_hours_df

            else:
                error_msg = 'Time out while getting contract details'
                self.logger.error(error_msg)
                raise BrokerException(error_msg)

    def get_contract_details(self, contract: IBContract) -> ContractDetails:
        with self.lock:
            self._reset_action_lock()
            request_id = 4
            self.client.reqContractDetails(request_id, contract)

            if self._wait_for_results():
                return self.wrapper.contract_details
            else:
                error_msg = 'Time out while getting contract details'
                self.logger.error(error_msg)
                raise BrokerException(error_msg)

    def place_orders(self, orders: Sequence[Order]) -> Sequence[int]:
        with self.orders_placement_lock:
            open_order_ids = {o.id for o in self.get_open_orders()}

            order_ids_list = []
            for order in orders:
                self.logger.info('Placing Order: {}'.format(order))
                order_id = self._execute_single_order(order) or self._find_newly_added_order_id(order, open_order_ids)
                if order_id is None:
                    error_msg = f"Not able to place order: {order}"
                    self.logger.error(error_msg)
                    raise BrokerException(error_msg)
                else:
                    order_ids_list.append(order_id)
            return order_ids_list

    def cancel_order(self, order_id: int):
        with self.lock:
            self.logger.info('Cancel order: {}'.format(order_id))
            self._reset_action_lock()
            self.wrapper.set_cancel_order_id(order_id)
            self.client.cancelOrder(order_id)

            if not self._wait_for_results():
                error_msg = 'Time out while cancelling order id {} : \n'.format(order_id)
                self.logger.error(error_msg)
                raise OrderCancellingException(error_msg)

    def get_open_orders(self) -> List[Order]:
        with self.lock:
            self._reset_action_lock()
            self.wrapper.reset_order_list()
            self.client.reqOpenOrders()

            if self._wait_for_results():
                return self.wrapper.order_list
            else:
                error_msg = 'Timeout while getting open orders'
                self.logger.error(error_msg)
                raise BrokerException(error_msg)

    def cancel_all_open_orders(self):
        """
        There is no way to check if cancelling of all orders was finished.
        One can only get open orders and confirm that the list is empty
        """
        with self.lock:
            self.client.reqGlobalCancel()
            self.logger.info('cancel_all_open_orders')

    def stop(self):
        """ Stop the Broker client and disconnect from the interactive brokers. """
        with self.lock:
            self.client.disconnect()
            self.logger.info("Disconnecting from the interactive brokers client")

    def _find_newly_added_order_id(self, order: Order, order_ids_existing_before: Set[int]):
        """ Given the list of order ids open before placing the given order, try to compute the id of the recently
         placed order. """
        orders_matching_given_order = {o.id for o in self.get_open_orders() if o == order}
        order_ids = orders_matching_given_order.difference(order_ids_existing_before)
        return next(iter(order_ids)) if len(order_ids) == 1 else None

    def _execute_single_order(self, order) -> Optional[int]:
        with self.lock:
            order_id = self.wrapper.next_order_id()

            self._reset_action_lock()
            self.wrapper.set_waiting_order_id(order_id)

            ib_contract = self.contract_ticker_mapper.ticker_to_contract(order.ticker)
            ib_order = self._to_ib_order(order)

            self.client.placeOrder(order_id, ib_contract, ib_order)
            if self._wait_for_results(10):
                return order_id

    def _wait_for_results(self, waiting_time: Optional[int] = None) -> bool:
        """ Wait for self.waiting_time """
        waiting_time = waiting_time or self.waiting_time
        wait_result = self.action_event_lock.wait(waiting_time)
        return wait_result

    def _reset_action_lock(self):
        """ threads calling wait() will block until set() is called"""
        self.action_event_lock.clear()

    def _to_ib_order(self, order: Order):
        ib_order = IBOrder()
        ib_order.action = 'BUY' if order.quantity > 0 else 'SELL'
        ib_order.totalQuantity = abs(order.quantity)

        ib_order = self._set_execution_style(ib_order, order.execution_style)

        time_in_force = order.time_in_force
        tif_str = self._map_to_tif_str(time_in_force)
        ib_order.tif = tif_str

        # this is necessery to set because of desupport of ETradeOnly and FirmQuoteOnly from api 10.10
        ib_order.eTradeOnly = ''
        ib_order.firmQuoteOnly = ''

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
        return ib_order
