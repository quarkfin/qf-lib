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

import os

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.analysis.strategy_monitoring.live_trading_sheet import LiveTradingSheet
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.common.utils.returns.is_return_stats import InSampleReturnStats
from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
from qf_lib.settings import Settings


def get_data():
    data_provider = container.resolve(QuandlDataProvider)  # type: QuandlDataProvider
    start_date = str_to_date('2017-01-01')
    end_date = str_to_date('2017-12-31')
    live_date = str_to_date('2016-01-01')

    dummy_strategy_tms = data_provider.get_price(
        tickers=QuandlTicker('AAPL', 'WIKI'), fields=PriceField.Close, start_date=start_date, end_date=end_date)
    dummy_benchmark_tms = data_provider.get_price(
        tickers=QuandlTicker('IBM', 'WIKI'), fields=PriceField.Close, start_date=start_date, end_date=end_date)

    dummy_strategy_tms.name = "Live Trading"
    dummy_benchmark_tms.name = "In-Sample Results"
    return dummy_strategy_tms, dummy_benchmark_tms, live_date


def main():
    this_dir_path = os.path.dirname(os.path.abspath(__file__))
    strategy_tms, benchmark_tms, live_date = cached_value(
        get_data, os.path.join(this_dir_path, 'live_trading_sheet.cache'))

    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter

    is_tms_stats = InSampleReturnStats(0.0005810136908445734, 0.012825939240219972)
    tearsheet = LiveTradingSheet(
        settings, pdf_exporter, strategy_tms, strategy_tms, is_tms_stats, "Live Trading Sheet demo")
    tearsheet.build_document()
    tearsheet.save()

    benchmark_tms.name = "Benchmark"
    leverage = strategy_tms  # does not make sense, but just to plot something
    tearsheet = LiveTradingSheet(
        settings, pdf_exporter, strategy_tms, leverage, is_tms_stats,
        "Live trading sheet demo - Benchmark", benchmark_tms=benchmark_tms)
    tearsheet.build_document()
    tearsheet.save()

    print("Finished")


if __name__ == '__main__':
    main()
