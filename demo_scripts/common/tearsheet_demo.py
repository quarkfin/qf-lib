import os

from qf_common.config.ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tearsheets.tearsheet_with_benchmark import TearsheetWithBenchmark
from qf_lib.common.tearsheets.tearsheet_without_benchmark import TearsheetWithoutBenchmark
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.settings import Settings


def get_data():
    data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider
    start_date = str_to_date('2010-01-01')
    end_date = str_to_date('2017-12-31')
    live_date = str_to_date('2016-01-01')

    strategy = data_provider.get_price(tickers=QuandlTicker('AAPL', 'WIKI'),
                                       fields=PriceField.Close, start_date=start_date, end_date=end_date)
    benchmark = data_provider.get_price(tickers=QuandlTicker('IBM', 'WIKI'),
                                        fields=PriceField.Close, start_date=start_date, end_date=end_date)

    strategy.name = "Strategy"
    benchmark.name = "Benchmark"

    return strategy, benchmark, live_date


this_dir_path = os.path.dirname(os.path.abspath(__file__))
strategy, benchmark, live_date = cached_value(get_data, os.path.join(this_dir_path, 'tearsheet4.cache'))


settings = container.resolve(Settings)  # type: Settings
pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter

tearsheet = TearsheetWithBenchmark(settings, pdf_exporter, strategy, benchmark, live_date=live_date,
                                   title="With Benchmark, With Live Date")
tearsheet.build_document()
tearsheet.save()

tearsheet = TearsheetWithBenchmark(settings, pdf_exporter, strategy, benchmark, live_date=None,
                                   title="With Benchmark, Without Live Date")
tearsheet.build_document()
tearsheet.save()

tearsheet = TearsheetWithoutBenchmark(settings, pdf_exporter, strategy, live_date=live_date,
                                      title="Without Benchmark, With Live Date")
tearsheet.build_document()
tearsheet.save()

tearsheet = TearsheetWithoutBenchmark(settings, pdf_exporter, strategy, live_date=None,
                                      title="Without Benchmark, Without Live Date")
tearsheet.build_document()
tearsheet.save()

print("Finished")
