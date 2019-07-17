import matplotlib.pyplot as plt

from qf_lib.backtesting.order.time_in_force import TimeInForce

plt.ion()  # required for dynamic chart, keep before other imports

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class BuyAndHoldStrategy(object):
    """
    A testing strategy that simply purchases (longs) an asset as soon as it starts and then holds until the completion
    of a backtest.
    """

    CONTRACT = Contract(symbol="SPY US Equity", security_type='STK', exchange='NASDAQ')
    TICKER = BloombergTicker("SPY US Equity")

    def __init__(self, broker: Broker, order_factory: OrderFactory, scheduler: Scheduler):
        self.order_factory = order_factory
        self.broker = broker

        self.invested = False

        scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        if not self.invested:
            orders = self.order_factory.percent_orders({self.CONTRACT: 1.0}, MarketOrder(), TimeInForce.GTC)

            self.broker.place_orders(orders)
            self.invested = True


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2018-01-01")

    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_backtest_name('Buy and Hold')
    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(BuyAndHoldStrategy.TICKER)

    BuyAndHoldStrategy(
        ts.broker,
        ts.order_factory,
        ts.notifiers.scheduler
    )

    ts.start_trading()


if __name__ == "__main__":
    main()
