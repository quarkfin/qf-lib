import os

from qf_common.config.ioc import container
from qf_lib.analysis.strategy_monitoring.live_trading_sheet import LiveTradingSheet
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.common.utils.returns.is_return_stats import InSampleReturnStats
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.settings import Settings


def get_data():
    data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider
    start_date = str_to_date('2017-01-01')
    end_date = str_to_date('2017-12-31')
    live_date = str_to_date('2016-01-01')

    strategy = data_provider.get_price(tickers=QuandlTicker('AAPL', 'WIKI'),
                                       fields=PriceField.Close, start_date=start_date, end_date=end_date)
    benchmark = data_provider.get_price(tickers=QuandlTicker('IBM', 'WIKI'),
                                        fields=PriceField.Close, start_date=start_date, end_date=end_date)

    strategy.name = "Live Trading"
    benchmark.name = "In-Sample Results"
    return strategy, benchmark, live_date


this_dir_path = os.path.dirname(os.path.abspath(__file__))
strategy, benchmark, live_date = cached_value(get_data, os.path.join(this_dir_path, 'live_trading_sheet.cache'))


settings = container.resolve(Settings)  # type: Settings
pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter

is_tms_stats = InSampleReturnStats(0.0005810136908445734, 0.012825939240219972)
tearsheet = LiveTradingSheet(settings, pdf_exporter, strategy, strategy, is_tms_stats, "Live Trading Sheet demo")
tearsheet.build_document()
tearsheet.save()

benchmark.name = "Benchmark"
leverage = strategy  # does not make sense, but just to plot something
tearsheet = LiveTradingSheet(settings, pdf_exporter, strategy, leverage, is_tms_stats,
                             "Live trading sheet demo - Benchmark", benchmark_tms=benchmark)
tearsheet.build_document()
tearsheet.save()

print("Finished")
