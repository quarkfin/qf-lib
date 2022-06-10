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
from unittest.mock import Mock, call

import pandas as pd

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.periodic_event.intraday_bar_event import IntradayBarEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.events.time_event.single_time_event.schedule_order_execution_event import \
    ScheduleOrderExecutionEvent
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class TestStopLossExecutionStyle(TestCase):
    MSFT_TICKER_STR = "MSFT US Equity"

    def setUp(self):
        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

        self.start_date = str_to_date("2018-02-04")
        self.number_of_minutes = 5

        before_close = self.start_date + MarketCloseEvent.trigger_time() - RelativeDelta(minutes=self.number_of_minutes)
        self.msft_ticker = BloombergTicker(self.MSFT_TICKER_STR)

        self.timer = SettableTimer(initial_time=before_close)

        self.data_handler = Mock(spec=DataHandler)
        self.data_handler.data_provider = Mock(spec=DataProvider)

        scheduler = Mock(spec=Scheduler)
        ScheduleOrderExecutionEvent.clear()

        # Set the periodic bar events to intraday trading
        IntradayBarEvent.frequency = Frequency.MIN_1

        commission_model = FixedCommissionModel(commission=0.0)
        self.monitor = Mock(spec=AbstractMonitor)
        self.portfolio = Mock(spec=Portfolio)
        self.portfolio.open_positions_dict = {}

        slippage_model = PriceBasedSlippage(0.0, self.data_handler)
        self.exec_handler = SimulatedExecutionHandler(self.data_handler, self.timer, scheduler, self.monitor,
                                                      commission_model, self.portfolio, slippage_model,
                                                      RelativeDelta(minutes=self.number_of_minutes))

        self._set_last_available_price(100.0)
        self.stop_loss_order_1 = Order(self.msft_ticker, quantity=-1, execution_style=StopOrder(95.0),
                                       time_in_force=TimeInForce.GTC)
        self.stop_loss_order_2 = Order(self.msft_ticker, quantity=-1, execution_style=StopOrder(90.0),
                                       time_in_force=TimeInForce.GTC)

        self.stop_loss_order_3 = Order(self.msft_ticker, quantity=-1, execution_style=StopOrder(50.0),
                                       time_in_force=TimeInForce.DAY)

        self.exec_handler.assign_order_ids([self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3])

    def _trigger_single_time_event(self):
        self.timer.set_current_time(self.timer.now() + RelativeDelta(minutes=self.number_of_minutes))
        event = ScheduleOrderExecutionEvent()
        self.exec_handler.on_orders_accept(event)

    def test_day_order_disappears_after_a_day(self):
        self._set_bar_for_today(open_price=105.0, high_price=110.0, low_price=100.0, close_price=105.0,
                                volume=100000000)
        self._trigger_single_time_event()

        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3]
        actual_orders = self.exec_handler.get_open_orders()
        assert_lists_equal(expected_orders, actual_orders)

        self.exec_handler.on_market_close(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2]
        assert_lists_equal(expected_orders, actual_orders)

    def test_no_orders_executed_on_market_open(self):
        # Move before the market open event
        self._set_bar_for_today(open_price=105.0, high_price=110.0, low_price=100.0, close_price=105.0,
                                volume=100000000.0)
        self.timer.set_current_time(self.timer.now() + MarketOpenEvent.trigger_time() -
                                    RelativeDelta(minutes=self.number_of_minutes))
        self.exec_handler.assign_order_ids([self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3])
        # Trigger the order execution event (the function also forwards time into the future)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3]
        assert_lists_equal(expected_orders, actual_orders)

    def test_order_not_executed_when_stop_price_not_hit(self):
        self._set_bar_for_today(open_price=105.0, high_price=110.0, low_price=100.0, close_price=105.0,
                                volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2]
        assert_lists_equal(expected_orders, actual_orders)

    def test_order_not_executed_when_bar_for_today_is_incomplete(self):
        self._set_bar_for_today(open_price=None, high_price=110.0, low_price=100.0, close_price=105.0,
                                volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        self.portfolio.transact_transaction.assert_not_called()
        self.monitor.record_transaction.assert_not_called()

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2]
        assert_lists_equal(expected_orders, actual_orders)

    def test_one_order_executed_when_one_stop_price_hit(self):
        self._set_bar_for_today(open_price=100.0, high_price=110.0, low_price=94.0, close_price=105.0,
                                volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([self.stop_loss_order_2], self.exec_handler.get_open_orders())

        expected_transaction = Transaction(self.timer.now(), self.msft_ticker, -1,
                                           self.stop_loss_order_1.execution_style.stop_price, 0.0)
        self.monitor.record_transaction.assert_called_once_with(expected_transaction)
        self.portfolio.transact_transaction.assert_called_once_with(expected_transaction)

    def test_both_orders_executed_when_both_stop_prices_hit(self):
        self._set_bar_for_today(open_price=100.0, high_price=110.0, low_price=90.0, close_price=105.0,
                                volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([], self.exec_handler.get_open_orders())

        expected_transactions = [
            Transaction(self.timer.now(), self.msft_ticker, -1, self.stop_loss_order_1.execution_style.stop_price, 0),
            Transaction(self.timer.now(), self.msft_ticker, -1, self.stop_loss_order_2.execution_style.stop_price, 0),
        ]
        self.monitor.record_transaction.assert_has_calls(call(t) for t in expected_transactions)
        self.portfolio.transact_transaction.assert_has_calls(call(t) for t in expected_transactions)

        self.assertEqual(self.monitor.record_transaction.call_count, 2)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 2)

    def test_market_opens_at_much_lower_price_than_it_closed_at_yesterday(self):
        self._set_bar_for_today(open_price=70.0, high_price=100.0, low_price=68.0, close_price=90.0, volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([], self.exec_handler.get_open_orders())
        expected_transactions = [
            Transaction(self.timer.now(), self.msft_ticker, -1, 70.0, 0),
            Transaction(self.timer.now(), self.msft_ticker, -1, 70.0, 0),
        ]
        self.monitor.record_transaction.assert_has_calls(call(t) for t in expected_transactions)
        self.portfolio.transact_transaction.assert_has_calls(call(t) for t in expected_transactions)

        self.assertEqual(self.monitor.record_transaction.call_count, 2)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 2)

    def test_market_opens_at_much_higher_price_than_it_closed_at_yesterday(self):
        self.buy_stop_loss_order = Order(self.msft_ticker, quantity=1, execution_style=StopOrder(120.0),
                                         time_in_force=TimeInForce.GTC)

        self.exec_handler.assign_order_ids([self.buy_stop_loss_order])
        self._set_bar_for_today(open_price=120.0, high_price=130.0, low_price=68.0, close_price=90.0,
                                volume=100000000.0)

        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([], self.exec_handler.get_open_orders())

        expected_transactions = [
            Transaction(self.timer.now(), self.msft_ticker, -1, self.stop_loss_order_1.execution_style.stop_price, 0),
            Transaction(self.timer.now(), self.msft_ticker, -1, self.stop_loss_order_2.execution_style.stop_price, 0),
            Transaction(self.timer.now(), self.msft_ticker, 1, 120, 0),

        ]
        self.monitor.record_transaction.assert_has_calls(call(t) for t in expected_transactions)
        self.portfolio.transact_transaction.assert_has_calls(call(t) for t in expected_transactions)

        self.assertEqual(self.monitor.record_transaction.call_count, 3)
        self.assertEqual(self.portfolio.transact_transaction.call_count, 3)

    def _set_last_available_price(self, price):
        def result(tickers):
            if tickers:
                return QFSeries(data=[price], index=pd.Index(tickers))
            else:
                return QFSeries()

        self.data_handler.get_last_available_price.side_effect = result

    def _set_bar_for_today(self, open_price, high_price, low_price, close_price, volume):
        self.data_handler.get_price.side_effect = lambda tickers, fields, start_date, end_date, frequency: \
            QFDataFrame(index=tickers, columns=fields, data=[[open_price, high_price, low_price, close_price, volume]])
