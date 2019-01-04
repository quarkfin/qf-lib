from unittest import TestCase

import matplotlib.pyplot as plt

from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_common.config.ioc import container
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class SpxWithStopLoss(object):
    ticker = BloombergTicker("SPX Index")
    percentage = 0.005

    def __init__(self, ts: BacktestTradingSession):
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.contract_ticker_mapper = ts.contract_ticker_mapper
        self.position_sizer = ts.position_sizer
        self.timer = ts.timer

        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        last_price = self.data_handler.get_last_available_price(self.ticker)

        contract = self.contract_ticker_mapper.ticker_to_contract(self.ticker)

        orders = self.order_factory.target_percent_orders({contract: 1.0}, MarketOrder(),
                                                          time_in_force=TimeInForce.OPG, tolerance_percent=0.02)

        stop_price = last_price * (1 - self.percentage)
        execution_style = StopOrder(stop_price=stop_price)
        stop_order = self.order_factory.percent_orders({contract: -1}, execution_style=execution_style,
                                                       time_in_force=TimeInForce.DAY)

        self.broker.cancel_all_open_orders()
        self.broker.place_orders(orders)
        self.broker.place_orders(stop_order)


def main():
    start_date = str_to_date("2017-01-01")
    end_date = str_to_date("2018-01-01")

    session_builder = BacktestTradingSessionBuilder(start_date, end_date)
    session_builder.set_backtest_name('SPY w. stop ' + str(SpxWithStopLoss.percentage))
    session_builder.set_initial_cash(1000000)
    ts = session_builder.build(container)
    ts.use_data_preloading(SpxWithStopLoss.ticker, RelativeDelta(days=40))

    SpxWithStopLoss(ts)
    ts.start_trading()

    actual_end_value = ts.portfolio.get_portfolio_timeseries()[-1]
    expected_value = 1137843

    print("Expected End Value = {}".format(expected_value))
    print("Actual End Value   = {}".format(actual_end_value))
    print("DIFF               = {}".format(expected_value - actual_end_value))

    test = TestCase()
    test.assertAlmostEqual(expected_value, actual_end_value, delta=10)


if __name__ == "__main__":
    main()
