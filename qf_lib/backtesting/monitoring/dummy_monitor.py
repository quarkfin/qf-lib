from datetime import datetime

from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.transaction import Transaction


class DummyMonitor(AbstractMonitor):

    def end_of_trading_update(self, timestamp: datetime):
        pass

    def end_of_day_update(self, timestamp: datetime):
        pass

    def real_time_update(self, timestamp: datetime):
        pass

    def record_transaction(self, transaction: Transaction):
        pass
