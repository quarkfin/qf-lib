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

import numpy as np

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.analysis.trade_analysis.trade_analysis_sheet import TradeAnalysisSheet
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.settings import Settings


def get_data():
    start_date = str_to_date('2017-01-01')
    end_date = str_to_date('2017-12-31')

    number_of_trades = 200
    ticker = BloombergTicker("MY_STOCK", SecurityType.STOCK, 1)
    trades = [
        Trade(start_date, end_date, ticker, pnl, 0, 1, pnl / 10000)
        for pnl in np.random.normal(0, 200, number_of_trades)
    ]
    return trades, 1, start_date, end_date


def main():
    this_dir_path = os.path.dirname(os.path.abspath(__file__))
    trades, nr_of_assets_traded, start_date, end_date = cached_value(
        get_data, os.path.join(this_dir_path, 'trade_analysis.cache'))

    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter
    nr_of_assets_traded = len(set(t.ticker.name for t in trades))

    trade_analysis_sheet = TradeAnalysisSheet(
        settings, pdf_exporter, nr_of_assets_traded, trades, start_date, end_date, title="Sample trade analysis")
    trade_analysis_sheet.build_document()
    trade_analysis_sheet.save()

    print("Finished")


if __name__ == '__main__':
    main()
