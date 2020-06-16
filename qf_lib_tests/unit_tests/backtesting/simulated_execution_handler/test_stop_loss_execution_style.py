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

from datetime import datetime
from unittest import TestCase

import pandas as pd
from mockito import mock, verify, spy, when, verifyZeroInteractions

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.bloomberg_mapper import \
    DummyBloombergContractTickerMapper
from qf_lib.backtesting.events.time_event.periodic_event.intraday_bar_event import IntradayBarEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.events.time_event.single_time_event.schedule_order_execution_event import ScheduleOrderExecutionEvent
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class _MonitorMock(AbstractMonitor):
    def __init__(self):
        # noinspection PyTypeChecker
        self.transactions = []

    def real_time_update(self, timestamp: datetime):
        raise NotImplementedError

    def end_of_day_update(self, timestamp: datetime):
        raise NotImplementedError

    def end_of_trading_update(self, timestamp: datetime = None):
        raise NotImplementedError

    def record_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)


class TestStopLossExecutionStyle(TestCase):
    MSFT_TICKER_STR = "MSFT US Equity"

    def setUp(self):

        MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
        MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

        self.start_date = str_to_date("2018-02-04")
        self.number_of_minutes = 5

        before_close = self.start_date + MarketCloseEvent.trigger_time() - \
            RelativeDelta(minutes=self.number_of_minutes)

        self.msft_contract = Contract(self.MSFT_TICKER_STR, security_type='STK', exchange='TEST')
        self.msft_ticker = BloombergTicker(self.MSFT_TICKER_STR)

        self.contracts_to_tickers_mapper = DummyBloombergContractTickerMapper()
        self.timer = SettableTimer(initial_time=before_close)

        self.data_handler = mock(strict=True)

        self.scheduler = mock()
        ScheduleOrderExecutionEvent.clear()

        # Set the periodic bar events to intraday trading
        IntradayBarEvent.frequency = Frequency.MIN_1

        self.commission_model = FixedCommissionModel(commission=0.0)
        self.monitor = _MonitorMock()
        self.spied_monitor = spy(self.monitor)
        self.portfolio = mock()

        slippage_model = PriceBasedSlippage(0.0)
        self.exec_handler = SimulatedExecutionHandler(self.data_handler, self.timer, self.scheduler, self.spied_monitor,
                                                      self.commission_model, self.contracts_to_tickers_mapper,
                                                      self.portfolio, slippage_model,
                                                      RelativeDelta(minutes=self.number_of_minutes))

        self._set_current_msft_price(100.0)
        self.stop_loss_order_1 = Order(self.msft_contract, quantity=-1, execution_style=StopOrder(95.0),
                                       time_in_force=TimeInForce.GTC)
        self.stop_loss_order_2 = Order(self.msft_contract, quantity=-1, execution_style=StopOrder(90.0),
                                       time_in_force=TimeInForce.GTC)

        self.stop_loss_order_3 = Order(self.msft_contract, quantity=-1, execution_style=StopOrder(50.0),
                                       time_in_force=TimeInForce.DAY)

        self.exec_handler.assign_order_ids([self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3])

    def _trigger_single_time_event(self):
        self.timer.set_current_time(self.timer.now() + RelativeDelta(minutes=self.number_of_minutes))
        event = ScheduleOrderExecutionEvent()
        self.exec_handler.on_orders_accept(event)

    def test_day_order_disappears_after_a_day(self):
        self._set_bar_for_today(open=105.0, high=110.0, low=100.0, close=105.0, volume=100000000.0)
        self._trigger_single_time_event()

        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3]
        actual_orders = self.exec_handler.get_open_orders()
        assert_lists_equal(expected_orders, actual_orders)

        self.exec_handler.on_market_close(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2]
        assert_lists_equal(expected_orders, actual_orders)

    def test_no_orders_executed_on_market_open(self):
        # Move before the market open event
        self._set_bar_for_today(open=105.0, high=110.0, low=100.0, close=105.0, volume=100000000.0)
        self.timer.set_current_time(self.timer.now() + MarketOpenEvent.trigger_time() -
                                    RelativeDelta(minutes=self.number_of_minutes))
        self.exec_handler.assign_order_ids([self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3])
        # Trigger the order execution event (the function also forwards time into the future)
        self._trigger_single_time_event()
        self.exec_handler.on_market_open(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2, self.stop_loss_order_3]
        assert_lists_equal(expected_orders, actual_orders)

    def test_order_not_executed_when_stop_price_not_hit(self):

        self._set_bar_for_today(open=105.0, high=110.0, low=100.0, close=105.0, volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2]
        assert_lists_equal(expected_orders, actual_orders)

    def test_order_not_executed_when_bar_for_today_is_incomplete(self):
        self._set_bar_for_today(open=None, high=110.0, low=100.0, close=105.0, volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_handler.get_open_orders()
        expected_orders = [self.stop_loss_order_1, self.stop_loss_order_2]
        assert_lists_equal(expected_orders, actual_orders)

    def test_one_order_executed_when_one_stop_price_hit(self):
        self._set_bar_for_today(open=100.0, high=110.0, low=94.0, close=105.0, volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([self.stop_loss_order_2], self.exec_handler.get_open_orders())
        verify(self.spied_monitor, times=1).record_transaction(...)
        verify(self.portfolio, times=1).transact_transaction(...)

        self.assertEqual(1, len(self.monitor.transactions))
        actual_transaction = self.monitor.transactions[0]

        self.assertEqual(self.msft_contract, actual_transaction.contract)
        self.assertEqual(-1, actual_transaction.quantity)
        self.assertEqual(self.stop_loss_order_1.execution_style.stop_price, actual_transaction.price)
        self.assertEqual(0.0, actual_transaction.commission)

    def test_both_orders_executed_when_both_stop_prices_hit(self):
        self._set_bar_for_today(open=100.0, high=110.0, low=90.0, close=105.0, volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([], self.exec_handler.get_open_orders())
        verify(self.spied_monitor, times=2).record_transaction(...)
        verify(self.portfolio, times=2).transact_transaction(...)

        self.assertEqual(2, len(self.monitor.transactions))

        actual_transaction_1 = self.monitor.transactions[0]
        self.assertEqual(self.msft_contract, actual_transaction_1.contract)
        self.assertEqual(-1, actual_transaction_1.quantity)
        self.assertEqual(self.stop_loss_order_1.execution_style.stop_price, actual_transaction_1.price)
        self.assertEqual(0.0, actual_transaction_1.commission)

        actual_transaction_2 = self.monitor.transactions[1]
        self.assertEqual(self.msft_contract, actual_transaction_2.contract)
        self.assertEqual(-1, actual_transaction_2.quantity)
        self.assertEqual(self.stop_loss_order_2.execution_style.stop_price, actual_transaction_2.price)
        self.assertEqual(0.0, actual_transaction_2.commission)

    def test_market_opens_at_much_lower_price_than_it_closed_at_yesterday(self):
        self._set_bar_for_today(open=70.0, high=100.0, low=68.0, close=90.0, volume=100000000.0)
        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([], self.exec_handler.get_open_orders())
        verify(self.spied_monitor, times=2).record_transaction(...)
        verify(self.portfolio, times=2).transact_transaction(...)

        self.assertEqual(2, len(self.monitor.transactions))

        actual_transaction_1 = self.monitor.transactions[0]
        self.assertEqual(self.msft_contract, actual_transaction_1.contract)
        self.assertEqual(-1, actual_transaction_1.quantity)
        self.assertEqual(70.0, actual_transaction_1.price)
        self.assertEqual(0.0, actual_transaction_1.commission)

        actual_transaction_2 = self.monitor.transactions[1]
        self.assertEqual(self.msft_contract, actual_transaction_2.contract)
        self.assertEqual(-1, actual_transaction_2.quantity)
        self.assertEqual(70.0, actual_transaction_2.price)
        self.assertEqual(0.0, actual_transaction_2.commission)

    def test_market_opens_at_much_higher_price_than_it_closed_at_yesterday(self):
        self.buy_stop_loss_order = Order(self.msft_contract, quantity=1, execution_style=StopOrder(120.0),
                                         time_in_force=TimeInForce.GTC)

        self.exec_handler.assign_order_ids([self.buy_stop_loss_order])
        self._set_bar_for_today(open=120.0, high=130.0, low=68.0, close=90.0, volume=100000000.0)

        self._trigger_single_time_event()
        self.exec_handler.on_market_close(...)

        assert_lists_equal([], self.exec_handler.get_open_orders())

        verify(self.spied_monitor, times=3).record_transaction(...)
        verify(self.portfolio, times=3).transact_transaction(...)

        self.assertEqual(3, len(self.monitor.transactions))

        actual_transaction_3 = self.monitor.transactions[2]
        self.assertEqual(self.msft_contract, actual_transaction_3.contract)
        self.assertEqual(1, actual_transaction_3.quantity)
        self.assertEqual(120.0, actual_transaction_3.price)
        self.assertEqual(0.0, actual_transaction_3.commission)

    def _set_current_msft_price(self, price):
        when(self.data_handler).get_last_available_price([self.msft_ticker]).thenReturn(
            pd.Series(data=[price], index=pd.Index([self.msft_ticker]), name=self.start_date)
        )

    def _set_bar_for_today(self, open, high, low, close, volume):
        when(self.data_handler).get_current_bar([self.msft_ticker]).thenReturn(
            pd.DataFrame(
                index=pd.Index([self.msft_ticker]), columns=PriceField.ohlcv(),
                data=[[open, high, low, close, volume]]
            )
        )
