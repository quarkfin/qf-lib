import matplotlib.pyplot as plt

from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.settings import Settings

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.enums.price_field import PriceField
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_common.config.ioc import container
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class SimpleMAStrategy(object):
    """
    A testing strategy that simply purchases (longs) an asset as soon as it starts and then holds until the completion
    of a backtest.
    """

    ticker = BloombergTicker("MSFT US Equity")

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
        long_ma_len = 20
        short_ma_len = 5

        long_ma_series = self.data_handler.historical_price(self.ticker, PriceField.Close, long_ma_len)
        long_ma_price = long_ma_series.mean()

        short_ma_series = long_ma_series.tail(short_ma_len)
        short_ma_price = short_ma_series.mean()

        contract = self.contract_ticker_mapper.ticker_to_contract(self.ticker)

        if short_ma_price >= long_ma_price:
            orders = self.order_factory.target_percent_orders({contract: 1.0}, MarketOrder())
        else:
            orders = self.order_factory.target_percent_orders({contract: 0.0}, MarketOrder())

        self.broker.cancel_all_open_orders()
        self.broker.place_orders(orders)


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2010-03-01")

    data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider
    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter
    excel_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter

    session_builder = BacktestTradingSessionBuilder(data_provider, settings, pdf_exporter, excel_exporter)
    session_builder.set_backtest_name('Simple_MA')
    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(SimpleMAStrategy.ticker, RelativeDelta(days=40))

    SimpleMAStrategy(ts)
    ts.start_trading()


if __name__ == "__main__":
    main()
