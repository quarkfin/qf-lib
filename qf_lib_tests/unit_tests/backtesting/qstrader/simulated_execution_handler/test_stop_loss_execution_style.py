from unittest import TestCase

from mockito import mock, when

from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.events.time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.execution_handler.simulated.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.monitoring.dummy_monitor import DummyMonitor
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer


class TestStopLossExecutionStyle(TestCase):
    def setUp(self):
        contracts_to_tickers_mapper = DummyBloombergContractTickerMapper()
        scheduler = mock(strict=True)
        when(scheduler).subscribe(MarketOpenEvent, scheduler).thenReturn(None)
        when(scheduler).subscribe(MarketCloseEvent, scheduler).thenReturn(None)

        data_handler = None  # TODO mock it
        commission_model = FixedCommissionModel(commission=0.0)
        monitor = DummyMonitor()
        # portfolio: Portfolio
        timer = SettableTimer(initial_time=str_to_date("2018-02-04"))
        portfolio = None  # TODO mock dummy Portfolio

        exec_hanlder = SimulatedExecutionHandler(data_handler, timer, scheduler, monitor,
                                                 commission_model, contracts_to_tickers_mapper, portfolio)

        self.execution_handler = None

    def test_stop_loss_executed_when_price_dropped_below_limit(self):
        pass