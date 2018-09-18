from abc import ABCMeta, abstractmethod
from datetime import datetime

from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.transaction import Transaction


class AbstractMonitor(metaclass=ABCMeta):
    """
    AbstractMonitor is a class providing an interface for
    all inherited Monitor classes (live, historic, custom, etc).
    Monitor should be subclassed according to the use.
    """

    def __init__(self, backtest_result: BacktestResult):
        self.backtest_result = backtest_result

    @abstractmethod
    def real_time_update(self, timestamp: datetime):
        """
        Update a basic statistics.
        This method should be light as it might be called after every transaction or price update
        """
        raise NotImplementedError("Should implement real_time_update()")

    @abstractmethod
    def end_of_day_update(self, timestamp: datetime):
        """
        Update the statistics after a whole day of trading. Should be used in live trading only
        """
        raise NotImplementedError("Should implement end_of_day_update()")

    @abstractmethod
    def end_of_trading_update(self, timestamp: datetime):
        """
        Final update at the end of backtest session
        """
        raise NotImplementedError("Should implement end_of_trading_update()")

    @abstractmethod
    def record_transaction(self, transaction: Transaction):
        """
        This method is called every time ExecutionHandler creates a new Transaction
        """
        raise NotImplementedError("Should implement record_transaction()")
