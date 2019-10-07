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


from datetime import datetime

from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.settings import Settings


class LightBacktestMonitor(BacktestMonitor):
    """
    This Monitor will be used to monitor backtest run from the script.
    It will display the portfolio value as the backtest progresses and generate a PDF at the end.
    It is not suitable for the Web application
    """

    def __init__(self, backtest_result: BacktestResult, settings: Settings,
                 pdf_exporter: PDFExporter, excel_exporter: ExcelExporter):
        super().__init__(backtest_result, settings, pdf_exporter, excel_exporter)

        self._nr_of_days = 20
        self._ctr = 0
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def end_of_day_update(self, timestamp: datetime = None):
        """
        Update line chart with current timeseries, buy only once in self._nr_of_days
        """
        self._ctr += 1

        if self._ctr % self._nr_of_days == 0:
            BacktestMonitor.end_of_day_update(self, timestamp)

    def record_transaction(self, transaction: Transaction):
        """ Do not record trades to save execution time, for more details use BacktestMonitor"""
        pass
