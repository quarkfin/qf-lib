import logging

import matplotlib.pyplot as plt
plt.ion()  # required for dynamic chart

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.backtesting.risk_manager.risk_manager import RiskManager
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_common.config import container
from qf_lib.backtesting.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.events.time_event.scheduler import Scheduler
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.settings import Settings


class BuyAndHoldStrategy(object):
    """
    A testing strategy that simply purchases (longs) an asset as soon as it starts and then holds until the completion
    of a backtest.
    """
    # MICROSOFT_TICKER = QuandlTicker("MSFT", "WIKI")
    # APPLE_TICKER = QuandlTicker("AAPL", "WIKI")

    MICROSOFT_CONTRACT = Contract(symbol="MSFT US Equity", security_type='STK', exchange='NASDAQ')
    MICROSOFT_TICKER = BloombergTicker("MSFT US Equity")

    def __init__(self, broker: Broker, order_factory: OrderFactory, position_sizer: PositionSizer,
                 risk_manager: RiskManager, scheduler: Scheduler):
        self.order_factory = order_factory
        self.broker = broker
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager

        self.invested = False

        scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        if not self.invested:
            initial_orders = self.order_factory.percent_order({self.MICROSOFT_CONTRACT: 1.0}, MarketOrder(),
                                                              time_in_force='DAY')
            sized_orders = self.position_sizer.size_orders(initial_orders)
            refined_orders = self.risk_manager.refine_orders(sized_orders)

            self.broker.place_orders(refined_orders)
            self.invested = True


def main():
    setup_logging(
        level=logging.INFO,
        console_logging=True
    )

    backtest_name = 'Buy and Hold'

    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2010-02-06")

    data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider
    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter
    excel_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter

    msft_prices = data_provider.get_price(
        BuyAndHoldStrategy.MICROSOFT_TICKER, fields=[PriceField.Open, PriceField.Close],
        start_date=str_to_date("2009-12-28"), end_date=str_to_date("2010-02-06")
    )

    first_trade_date = msft_prices.loc[start_date:].first_valid_index()
    initial_cash = msft_prices.loc[:, PriceField.Open].asof(first_trade_date)

    ts = BacktestTradingSession(
        backtest_name=backtest_name,
        settings=settings,
        data_provider=data_provider,
        contract_ticker_mapper=DummyBloombergContractTickerMapper(),
        pdf_exporter=pdf_exporter,
        excel_exporter=excel_exporter,
        start_date=start_date,
        end_date=end_date,
        initial_cash=initial_cash
    )

    BuyAndHoldStrategy(
        ts.broker,
        ts.order_factory,
        ts.position_sizer,
        ts.risk_manager,
        ts.notifiers.scheduler
    )

    ts.start_trading()

if __name__ == "__main__":
    main()
