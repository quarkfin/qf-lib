import logging
from datetime import datetime

from os.path import join

from qf_common.config import container
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.settings import Settings
from scripts.backtesting.qstrader.strategies.LongShortVol.vol_long_short_etn_strategy import VolLongShortUsingETN


def main():
    setup_logging(
        level=logging.INFO,
        console_logging=True
    )

    backtest_name = 'Volatility Strategy'

    start_date = str_to_date("2014-01-01")
    end_date = str_to_date("2014-01-31")

    data_provider = container.resolve(GeneralPriceProvider)  # type: GeneralPriceProvider
    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter
    excel_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter
    initial_cash = 1000000
    trading_session = BacktestTradingSession(
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

    VolLongShortUsingETN(trading_session, use_stop_loss=False)

    # Set up the backtest
    trading_session.start_trading()

    export_to_excel(trading_session.portfolio.get_portfolio_timeseries(), backtest_name)


def export_to_excel(portfolio_tms, backtest_name):
    portfolio_tms.name = backtest_name
    xl_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter
    settings = container.resolve(Settings)

    name_template = "%Y_%m_%d-%H%M {} TMS.xlsx".format(backtest_name)
    xlx_file_path = join(settings.output_directory, 'Backtest', datetime.now().strftime(name_template))

    xl_exporter.export_container(portfolio_tms, xlx_file_path, starting_cell='A1', include_column_names=True)


if __name__ == "__main__":
    main()
