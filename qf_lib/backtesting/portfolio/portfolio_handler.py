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

from qf_lib.backtesting.events.time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.portfolio.portfolio import Portfolio


class PortfolioHandler(object):
    """
    The PortfolioHandler is designed to interact with the backtesting or live trading overall event-driven
    architecture. Each PortfolioHandler contains a Portfolio object, which stores the actual BacktestPosition objects.

    The PortfolioHandler takes a handle to the AbstractMonitor, which updates the statistics after a day of trading.
    """

    def __init__(self, portfolio: Portfolio, monitor: AbstractMonitor, scheduler: Scheduler):
        self.portfolio = portfolio
        self.monitor = monitor

        scheduler.subscribe(AfterMarketCloseEvent, listener=self)

    def on_after_market_close(self, event: TimeEvent):
        self.portfolio.update()
        self.monitor.end_of_day_update(event.time)
