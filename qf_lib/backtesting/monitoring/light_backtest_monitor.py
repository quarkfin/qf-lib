# it is important to import the matplotlib first and then switch the interactive/dynamic mode on.
import matplotlib.pyplot as plt

from qf_lib.common.enums.frequency import Frequency
from qf_lib.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis

plt.ion()  # required for dynamic chart

from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings
from datetime import datetime
from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from os import path


class LightBacktestMonitor(BacktestMonitor):
    """
    This Monitor will be used to monitor backtest run from the script.
    It will display the portfolio value as the backtest progresses and generate a PDF at the end.
    It is not suitable for the Web application
    """

    def __init__(self, backtest_result: BacktestResult, settings: Settings,
                 pdf_exporter: PDFExporter, excel_exporter: ExcelExporter):
        super().__init__(backtest_result, settings, pdf_exporter, excel_exporter)

        self._nr_of_days = 10
        self._ctr = 0

    def end_of_day_update(self, timestamp: datetime=None):
        """
        Update line chart with current timeseries, buy only once in self._nr_of_days
        """
        self._ctr += 1

        if self._ctr % self._nr_of_days == 0:
            BacktestMonitor.end_of_day_update(self, timestamp)

    def end_of_trading_update(self, _: datetime=None):
        """
        Saves the timeseries of the portfolio in the excel file
        """
        portfolio_tms = self.backtest_result.portfolio.get_portfolio_timeseries()
        portfolio_tms.name = self.backtest_result.backtest_name

        xlsx_filename = "{}.xlsx".format(self._file_name_template)
        relative_file_path = path.join("timeseries", xlsx_filename)
        self._excel_exporter.export_container(portfolio_tms, relative_file_path,
                                              starting_cell='A1', include_column_names=True)
        self._close_csv_file()

        ta = TimeseriesAnalysis(portfolio_tms, frequency=Frequency.DAILY)
        print(TimeseriesAnalysis.values_in_table(ta))



    def record_trade(self, transaction: Transaction):
        """ Do not record trades to save execution time, for more details use BacktestMonitor"""
        pass
