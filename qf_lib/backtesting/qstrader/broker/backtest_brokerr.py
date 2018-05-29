from typing import List, Optional

from qf_lib.backtesting.qstrader.portfolio.portfolio import Portfolio
from qf_lib.interactive_brokers.ib_utils import IBOrderInfo, AbstractPosition


class BacktestBroker(object):
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

    def get_portfolio_value(self) -> Optional[float]:
        return self.portfolio.current_portfolio_value

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

    def get_positions(self) -> Optional[List[AbstractPosition]]:
        return list(self.portfolio.open_positions_dict.values())

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
        pass


