from datetime import datetime
from unittest import TestCase

import pandas as pd
from mockito import mock, verify, spy, when, verifyZeroInteractions
from mockito.matchers import Matcher

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import PriceBasedSlippage
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import MarketOrder, MarketOnCloseOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib_tests.helpers.testing_tools.containers_comparison import assert_lists_equal


class _ArgCaptor(Matcher):
    def __init__(self):
        self.value = None

    def matches(self, arg):
        self.value = arg
        return True

    def get_value(self):
        return self.value


class _MonitorMock(AbstractMonitor):
    def __init__(self):
        # noinspection PyTypeChecker
        self.transactions = []

    def real_time_update(self, timestamp: datetime):
        raise NotImplementedError

    def end_of_day_update(self, timestamp: datetime):
        raise NotImplementedError

    def end_of_trading_update(self, timestamp: datetime):
        raise NotImplementedError

    def record_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)


class TestMarketOnOpenExecutionStyle(TestCase):
    MSFT_TICKER_STR = "MSFT US Equity"

    def setUp(self):
        self.start_date = str_to_date("2018-02-04")
        self.msft_contract = Contract(self.MSFT_TICKER_STR, security_type='SEK', exchange='TEST')
        self.msft_ticker = BloombergTicker(self.MSFT_TICKER_STR)

        self.contracts_to_tickers_mapper = DummyBloombergContractTickerMapper()
        self.timer = SettableTimer(initial_time=self.start_date)

        self.data_handler = mock(strict=True)

        self.scheduler = mock()

        self.commission_model = FixedCommissionModel(commission=0.0)
        self.monitor = _MonitorMock()
        self.spied_monitor = spy(self.monitor)
        self.portfolio = mock()

        slippage_model = PriceBasedSlippage(0.0)
        self.exec_hanlder = SimulatedExecutionHandler(self.data_handler, self.timer, self.scheduler, self.spied_monitor,
                                                      self.commission_model, self.contracts_to_tickers_mapper,
                                                      self.portfolio, slippage_model)

        self._set_last_msft_price(100.0)
        self.order_1 = Order(self.msft_contract, quantity=10, execution_style=MarketOrder(),
                             time_in_force=TimeInForce.OPG)
        self.order_2 = Order(self.msft_contract, quantity=-5, execution_style=MarketOrder(),
                             time_in_force=TimeInForce.OPG)
        self.order_3 = Order(self.msft_contract, quantity=-7, execution_style=MarketOrder(),
                             time_in_force=TimeInForce.OPG)

        self.order_4 = Order(self.msft_contract, quantity=4, execution_style=MarketOnCloseOrder(),
                             time_in_force=TimeInForce.DAY)

    def test_1_order_fill(self):
        self.exec_hanlder.accept_orders([self.order_1])
        self._set_price_for_now(101)
        self.exec_hanlder.on_market_open(...)

        verify(self.spied_monitor, times=1).record_transaction(...)
        verify(self.portfolio, times=1).transact_transaction(...)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_3_orders_fill(self):
        self.exec_hanlder.accept_orders([self.order_1, self.order_2, self.order_3])
        self._set_price_for_now(101)
        self.exec_hanlder.on_market_open(...)

        verify(self.spied_monitor, times=3).record_transaction(...)
        verify(self.portfolio, times=3).transact_transaction(...)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_3_orders_fill_only_at_open(self):
        self.exec_hanlder.accept_orders([self.order_1, self.order_2, self.order_3])
        self._set_price_for_now(101)
        self.exec_hanlder.on_market_close(...)

        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = [self.order_1, self.order_2, self.order_3]
        assert_lists_equal(expected_orders, actual_orders)

    def test_fill_open_and_close(self):
        self.exec_hanlder.accept_orders([self.order_1, self.order_2])
        self.exec_hanlder.accept_orders([self.order_2, self.order_3])
        self.exec_hanlder.accept_orders([self.order_3, self.order_4])
        self.exec_hanlder.accept_orders([self.order_4, self.order_4])

        self._set_price_for_now(101)
        self.exec_hanlder.on_market_open(...)

        verify(self.spied_monitor, times=5).record_transaction(...)
        verify(self.portfolio, times=5).transact_transaction(...)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = [self.order_4,  self.order_4,  self.order_4]
        assert_lists_equal(expected_orders, actual_orders)

        self.exec_hanlder.on_market_close(...)

        verify(self.spied_monitor, times=8).record_transaction(...)
        verify(self.portfolio, times=8).transact_transaction(...)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_fill_close_and_open(self):
        self.exec_hanlder.accept_orders([self.order_1, self.order_2])
        self.exec_hanlder.accept_orders([self.order_2, self.order_3])
        self.exec_hanlder.accept_orders([self.order_3, self.order_4])
        self.exec_hanlder.accept_orders([self.order_4, self.order_4])

        self._set_price_for_now(101)
        self.exec_hanlder.on_market_close(...)

        verify(self.spied_monitor, times=3).record_transaction(...)
        verify(self.portfolio, times=3).transact_transaction(...)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = [self.order_1,  self.order_2,  self.order_2, self.order_3, self.order_3]
        assert_lists_equal(expected_orders, actual_orders)

        self.exec_hanlder.on_market_open(...)

        verify(self.spied_monitor, times=8).record_transaction(...)
        verify(self.portfolio, times=8).transact_transaction(...)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = []
        assert_lists_equal(expected_orders, actual_orders)

    def test_market_open_transaction(self):
        order = self.order_1
        price = 102
        self.exec_hanlder.accept_orders([order])
        self._set_price_for_now(price)
        self.exec_hanlder.on_market_open(...)

        timestamp = self.timer.now()
        contract = order.contract
        quantity = order.quantity
        commission = self.commission_model.calculate_commission(order, price)
        expected_transaction = Transaction(timestamp, contract, quantity, price, commission)

        captor = _ArgCaptor()
        verify(self.spied_monitor, times=1).record_transaction(captor)
        self.assertEqual(expected_transaction, captor.get_value())

    def test_market_close_transaction(self):
        order = self.order_4
        price = 102
        self.exec_hanlder.accept_orders([self.order_1, order])
        self._set_price_for_now(price)
        self.exec_hanlder.on_market_close(...)

        timestamp = self.timer.now()
        contract = order.contract
        quantity = order.quantity
        commission = self.commission_model.calculate_commission(order, price)
        expected_transaction = Transaction(timestamp, contract, quantity, price, commission)

        captor = _ArgCaptor()
        verify(self.spied_monitor, times=1).record_transaction(captor)
        self.assertEqual(expected_transaction, captor.get_value())

    def test_market_close_does_not_trade(self):
        price = None
        self.exec_hanlder.accept_orders([self.order_1, self.order_4])
        self._set_price_for_now(price)
        self.exec_hanlder.on_market_close(...)

        verifyZeroInteractions(self.portfolio, self.spied_monitor)

    def test_market_open_does_not_trade(self):
        price = None
        self.exec_hanlder.accept_orders([self.order_1, self.order_4])
        self._set_price_for_now(price)
        self.exec_hanlder.on_market_open(...)

        verifyZeroInteractions(self.portfolio, self.spied_monitor)

    def _set_last_msft_price(self, price):
        when(self.data_handler).get_last_available_price([self.msft_ticker]).thenReturn(
            pd.Series(data=[price], index=pd.Index([self.msft_ticker]), name=self.start_date)
        )

    def _set_price_for_now(self, price):
        when(self.data_handler).get_current_price([self.msft_ticker]).thenReturn(
            pd.Series(data=[price], index=pd.Index([self.msft_ticker]))
        )

