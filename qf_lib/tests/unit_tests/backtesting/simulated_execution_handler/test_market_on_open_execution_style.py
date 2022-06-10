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

from unittest import TestCase
from unittest.mock import Mock

import pandas as pd

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.events.time_event.single_time_event.schedule_order_execution_event import \
    ScheduleOrderExecutionEvent
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import MarketOrder, MarketOnCloseOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class TestMarketOnOpenExecutionStyle(TestCase):
    MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
    MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

    def setUp(self):
        self.scheduling_time_delay = 1
        start_date = str_to_date("2018-02-04")

        before_close = start_date + MarketCloseEvent.trigger_time() - RelativeDelta(minutes=self.scheduling_time_delay)
        self.timer = SettableTimer(initial_time=before_close)

        self.msft_ticker = BloombergTicker("MSFT US Equity")

        self.data_handler = Mock(spec=DataHandler)
        self.data_handler.frequency = Frequency.DAILY
        self.data_handler.data_provider = Mock(spec=DataProvider)

        self.scheduler = Mock(spec=Scheduler)

        self.commission_model = FixedCommissionModel(commission=0.0)
        self.monitor = Mock(spec=AbstractMonitor)
        self.portfolio = Mock(spec=Portfolio)
        self.portfolio.open_positions_dict = {}

        slippage_model = PriceBasedSlippage(0.0, self.data_handler)
        self.exec_handler = SimulatedExecutionHandler(self.data_handler, self.timer, self.scheduler, self.monitor,
                                                      self.commission_model, self.portfolio, slippage_model,
                                                      RelativeDelta(minutes=self.scheduling_time_delay))

        self.order_1 = Order(self.msft_ticker, quantity=10, execution_style=MarketOrder(),
                             time_in_force=TimeInForce.OPG)
        self.order_2 = Order(self.msft_ticker, quantity=-5, execution_style=MarketOrder(),
                             time_in_force=TimeInForce.OPG)
        self.order_3 = Order(self.msft_ticker, quantity=-7, execution_style=MarketOrder(),
                             time_in_force=TimeInForce.OPG)

        self.order_4 = Order(self.msft_ticker, quantity=4, execution_style=MarketOnCloseOrder(),
                             time_in_force=TimeInForce.DAY)

    def _trigger_single_time_event(self):
        self.timer.set_current_time(self.timer.now() + RelativeDelta(minutes=self.scheduling_time_delay))
        event = ScheduleOrderExecutionEvent()
        self.exec_handler.on_orders_accept(event)

    def test_1_order_fill(self):
        self.exec_handler.assign_order_ids([self.order_1])
        self._set_current_price(101)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)

        self.monitor.record_transaction.assert_called_once()
        self.portfolio.transact_transaction.assert_called_once()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_3_orders_fill(self):
        self.exec_handler.assign_order_ids([self.order_1, self.order_2, self.order_3])
        self._set_current_price(101)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)

        self.assertEqual(self.monitor.record_transaction.call_count, 3)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 3)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_3_orders_fill_only_at_open(self):
        self.exec_handler.assign_order_ids([self.order_1, self.order_2, self.order_3])
        self._set_current_price(101)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.order_1, self.order_2, self.order_3]
        self.assertCountEqual(expected_orders, actual_orders)

    def test_fill_open_and_close(self):
        self.exec_handler.assign_order_ids([self.order_1, self.order_2])
        self.exec_handler.assign_order_ids([self.order_2, self.order_3])
        self.exec_handler.assign_order_ids([self.order_3, self.order_4])
        self.exec_handler.assign_order_ids([self.order_4, self.order_4])

        self._set_current_price(101)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)

        self.assertEqual(self.monitor.record_transaction.call_count, 3)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 3)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.order_4]
        assert_lists_equal(expected_orders, actual_orders)

        self.exec_handler.on_market_close(...)

        self.assertEqual(self.monitor.record_transaction.call_count, 4)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 4)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_fill_close_and_open(self):
        self.exec_handler.assign_order_ids([self.order_1, self.order_2])
        self.exec_handler.assign_order_ids([self.order_2, self.order_3])
        self.exec_handler.assign_order_ids([self.order_3, self.order_4])
        self.exec_handler.assign_order_ids([self.order_4, self.order_4])

        self._set_current_price(101)

        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        # Transaction related to order 4 will be executed only once, as only one Order object was passed
        self.monitor.record_transaction.assert_called_once()
        self.portfolio.transact_transaction.assert_called_once()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.order_1, self.order_2, self.order_3]
        self.assertCountEqual(expected_orders, actual_orders)

        self.exec_handler.on_market_open(...)

        self.assertEqual(self.monitor.record_transaction.call_count, 4)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 4)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = []
        self.assertCountEqual(expected_orders, actual_orders)

    def test_market_open_transaction(self):
        order = self.order_1
        price = 102
        self.exec_handler.assign_order_ids([order])
        self._set_current_price(price)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)

        timestamp = self.timer.now()
        ticker = order.ticker
        quantity = order.quantity
        commission = self.commission_model.calculate_commission(ticker, price)
        expected_transaction = Transaction(timestamp, ticker, quantity, price, commission)

        self.monitor.record_transaction.assert_called_once_with(expected_transaction)

    def test_market_close_transaction(self):
        order = self.order_4
        price = 102
        self.exec_handler.assign_order_ids([self.order_1, order])
        self._set_current_price(price)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        timestamp = self.timer.now()
        ticker = order.ticker
        quantity = order.quantity
        commission = self.commission_model.calculate_commission(order, price)
        expected_transaction = Transaction(timestamp, ticker, quantity, price, commission)

        self.monitor.record_transaction.assert_called_once_with(expected_transaction)

    def test_market_close_does_not_trade(self):
        price = None
        self.exec_handler.assign_order_ids([self.order_1, self.order_4])
        self._set_current_price(price)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

    def test_market_open_does_not_trade(self):
        price = None
        self.exec_handler.assign_order_ids([self.order_1, self.order_4])
        self._set_current_price(price)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

    def _set_last_available_price(self, price):
        self.data_handler.get_last_available_price.side_effect = lambda t: QFSeries([price],
                                                                                    index=pd.Index([self.msft_ticker]))

    def _set_current_price(self, price):
        self.data_handler.data_provider.get_price.side_effect = lambda a, b, c, d, e: \
            QFSeries(data=[price], index=[self.msft_ticker])
