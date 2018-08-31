from qf_lib.backtesting.events.time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.portfolio.portfolio import Portfolio


class PortfolioHandler(object):
    """
    The PortfolioHandler is designed to interact with the backtesting or live trading overall event-driven
    architecture. Each PortfolioHandler contains a Portfolio object, which stores the actual BacktestPosition objects.

    The PortfolioHandler takes a handle to a PositionSizer object which determines a mechanism, based on the current
    Portfolio, as to how to size a new Order.

    The PortfolioHandler also takes a handle to the RiskManager, which is used to modify any generated
    Orders to remain in line with risk parameters.
    """

    def __init__(self, portfolio: Portfolio, monitor: AbstractMonitor, scheduler: Scheduler):
        self.portfolio = portfolio
        self.monitor = monitor

        scheduler.subscribe(AfterMarketCloseEvent, listener=self)

    def on_after_market_close(self, event: TimeEvent):
        self.portfolio.update()
        self.monitor.end_of_day_update(event.time)
