from datetime import datetime

from qf_lib.backtesting.qstrader.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent
from qf_lib.backtesting.qstrader.monitoring.abstract_monitor import AbstractMonitor


class DummyMonitor(AbstractMonitor):

    def __init__(self, backtest_result: BacktestResult):
        super().__init__(backtest_result)

    def end_of_trading_update(self, timestamp: datetime):
        pass

    def end_of_day_update(self, timestamp: datetime):
        pass

    def real_time_update(self, timestamp: datetime):
        pass

    def record_trade(self, fill_event: FillEvent):
        pass
