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

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.analysis.tearsheets.tearsheet_comparative import TearsheetComparative
from qf_lib.analysis.tearsheets.tearsheet_with_benchmark import TearsheetWithBenchmark
from qf_lib.analysis.tearsheets.tearsheet_without_benchmark import TearsheetWithoutBenchmark
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings
from qf_lib.starting_dir import set_starting_dir_abs_path


def get_data():
    data_provider = daily_data_provider
    start_date = str_to_date('2013-01-01')
    end_date = str_to_date('2017-12-31')
    live_date = str_to_date('2015-01-01')

    strategy = data_provider.get_price(tickers=DummyTicker('AAA'),
                                       fields=PriceField.Close, start_date=start_date, end_date=end_date)
    benchmark = data_provider.get_price(tickers=DummyTicker('BBB'),
                                        fields=PriceField.Close, start_date=start_date, end_date=end_date)

    strategy.name = "Strategy"
    benchmark.name = "Benchmark"

    return strategy, benchmark, live_date


def main():
    # set the starting directory path below unless you set environment variable QF_STARTING_DIRECTORY to proper value
    set_starting_dir_abs_path(r"absolute/path/to/qf-lib")

    setup_logging(logging.INFO)
    this_dir_path = os.path.dirname(os.path.abspath(__file__))
    strategy, benchmark, live_date = cached_value(get_data, os.path.join(this_dir_path, 'tearsheet.cache'))

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
