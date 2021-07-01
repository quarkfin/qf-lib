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

import logging
import os

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.analysis.tearsheets.tearsheet_comparative import TearsheetComparative
from qf_lib.analysis.tearsheets.tearsheet_with_benchmark import TearsheetWithBenchmark
from qf_lib.analysis.tearsheets.tearsheet_without_benchmark import TearsheetWithoutBenchmark
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings


def get_data():
    data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider
    start_date = str_to_date('2010-01-01')
    end_date = str_to_date('2017-12-31')
    live_date = str_to_date('2015-01-01')

    strategy = data_provider.get_price(tickers=QuandlTicker('AAPL', 'WIKI'),
                                       fields=PriceField.Close, start_date=start_date, end_date=end_date)
    benchmark = data_provider.get_price(tickers=QuandlTicker('IBM', 'WIKI'),
                                        fields=PriceField.Close, start_date=start_date, end_date=end_date)

    strategy.name = "Strategy"
    benchmark.name = "Benchmark"

    return strategy, benchmark, live_date


def main():
    setup_logging(logging.INFO)
    this_dir_path = os.path.dirname(os.path.abspath(__file__))
    strategy, benchmark, live_date = cached_value(get_data, os.path.join(this_dir_path, 'tearsheet5.cache'))

    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter

    title = "Tearsheet With Benchmark, With Live Date"
    tearsheet = TearsheetWithBenchmark(
        settings, pdf_exporter, strategy, benchmark, live_date=live_date, title=title)
    tearsheet.build_document()
    tearsheet.save(file_name=title)

    title = "Tearsheet With Benchmark, Without Live Date"
    tearsheet = TearsheetWithBenchmark(
        settings, pdf_exporter, strategy, benchmark, live_date=None, title=title)
    tearsheet.build_document()
    tearsheet.save(file_name=title)

    title = "Tearsheet Without Benchmark, With Live Date"
    tearsheet = TearsheetWithoutBenchmark(
        settings, pdf_exporter, strategy, live_date=live_date, title=title)
    tearsheet.build_document()
    tearsheet.save(file_name=title)

    title = "Tearsheet Without Benchmark, Without Live Date"
    tearsheet = TearsheetWithoutBenchmark(
        settings, pdf_exporter, strategy, live_date=None, title=title)
    tearsheet.build_document()
    tearsheet.save(file_name=title)

    title = "Tearsheet Comparative"
    tearsheet = TearsheetComparative(settings, pdf_exporter, strategy, benchmark, title=title)
    tearsheet.build_document()
    tearsheet.save(file_name=title)

    print("Finished")


if __name__ == '__main__':
    main()
