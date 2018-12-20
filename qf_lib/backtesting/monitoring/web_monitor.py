from datetime import datetime

from geneva_analytics.data_providers.timeseries_data_provider import TimeseriesDataProvider
from geneva_analytics.web_api.backend.models import StrategyRun
from geneva_analytics.web_api.backend.src.dao.portfolio_dao import PortfolioDAO
from geneva_analytics.web_api.backend.src.dao.strategy_run_dao import StrategyRunDAO
from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency


class WebMonitor(AbstractMonitor):
    def __init__(self, backtest_result: BacktestResult, strategy_run: StrategyRun):
        self.backtest_result = backtest_result
        self._strategy_run = strategy_run
        self._tms_id = self._strategy_run.portfolio_value.id
        self._data_provider = TimeseriesDataProvider()

    def end_of_trading_update(self, _: datetime=None):
        """
        Saves the end portfolio and marks the strategy as not running
        """
        leverage_series = self.backtest_result.portfolio.leverage()
        db_leverage = self._data_provider.add_timeseries(
            self._strategy_run.portfolio_value.name + " leverage", "Leverage", Frequency.DAILY,
            leverage_series)

        db_portfolio = PortfolioDAO.save(self.backtest_result.portfolio,
                                         self._strategy_run.portfolio_value, db_leverage)
        StrategyRunDAO.finish(self._strategy_run.id, portfolio=db_portfolio, is_running=False, succeeded=True)

    def end_of_day_update(self, timestamp: datetime=None):
        """
        Adds the latest days data to the timeseries
        """
        portfolio = self.backtest_result.portfolio
        self._data_provider.add_timeseries_data_point(self._tms_id, portfolio.portfolio_values[-1], portfolio.dates[-1])

    def real_time_update(self, timestamp: datetime=None):
        """
        This method will not be used by the historical backtest
        """
        pass

    def record_transaction(self, transaction: Transaction):
        """
        WebMonitor doesn't have to do anything with recording Transactions
        """
        pass
