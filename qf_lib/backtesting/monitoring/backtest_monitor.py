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

import csv
from datetime import datetime
from io import TextIOWrapper
from os import path, makedirs
from typing import Optional, Tuple

import matplotlib.pyplot as plt

from qf_lib.analysis.exposure_analysis.exposure_settings import ExposureSettings
from qf_lib.analysis.exposure_analysis.exposure_generator import ExposureGenerator
from qf_lib.analysis.exposure_analysis.exposure_sheet import ExposureSheet
from qf_lib.analysis.tearsheets.portfolio_analysis_sheet import PortfolioAnalysisSheet
from qf_lib.common.utils.config_exporter import ConfigExporter
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.analysis.tearsheets.tearsheet_with_benchmark import TearsheetWithBenchmark
from qf_lib.analysis.tearsheets.tearsheet_without_benchmark import TearsheetWithoutBenchmark
from qf_lib.analysis.timeseries_analysis.timeseries_analysis import TimeseriesAnalysis
from qf_lib.analysis.trade_analysis.trade_analysis_sheet import TradeAnalysisSheet
from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class BacktestMonitorSettings:
    def __init__(self, issue_tearsheet=True, issue_portfolio_analysis_sheet=True, issue_trade_analysis_sheet=True,
                 issue_transaction_log=True, issue_signal_log=True, issue_config_log=True,
                 issue_daily_portfolio_values_file=True, print_stats_to_console=True,
                 generate_pnl_chart_per_ticker_in_portfolio_analysis=True,
                 display_live_backtest_progress=True, live_backtest_chart_refresh_frequency=20,
                 exposure_settings: ExposureSettings = None):
        self.issue_tearsheet = issue_tearsheet
        self.issue_portfolio_analysis_sheet = issue_portfolio_analysis_sheet
        self.issue_trade_analysis_sheet = issue_trade_analysis_sheet
        self.issue_transaction_log = issue_transaction_log
        self.issue_signal_log = issue_signal_log
        self.issue_config_log = issue_config_log
        self.issue_daily_portfolio_value_file = issue_daily_portfolio_values_file
        self.print_stats_to_console = print_stats_to_console
        self.generate_pnl_chart_per_ticker_in_portfolio_analysis = generate_pnl_chart_per_ticker_in_portfolio_analysis
        self.display_live_backtest_progress = display_live_backtest_progress
        self.live_backtest_chart_refresh_frequency = int(live_backtest_chart_refresh_frequency)
        self.exposure_settings = exposure_settings

    @staticmethod
    def no_stats() -> "BacktestMonitorSettings":
        """"
        Creates Settings that will generate no monitor output
        """
        return BacktestMonitorSettings(False, False, False, False, False, False, False, False, False, False, 20, None)


class BacktestMonitor(AbstractMonitor):
    """
    This Monitor will be used to monitor backtest run from the script.
    It will display the portfolio value as the backtest progresses and generate a PDF at the end.
    It is not suitable for the Web application
    """

    def __init__(self, backtest_result: BacktestResult, settings: Settings, pdf_exporter: PDFExporter,
                 excel_exporter: ExcelExporter, monitor_settings=None, benchmark_tms: QFSeries = None):

        self.backtest_result = backtest_result
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self._settings = settings
        self._pdf_exporter = pdf_exporter
        self._excel_exporter = excel_exporter
        self._signals_register = backtest_result.signals_register

        # set full display details if no setting is provided
        self._monitor_settings = BacktestMonitorSettings() if monitor_settings is None else monitor_settings
        self.benchmark_tms = benchmark_tms

        sub_dir_name = datetime.now().strftime("%Y_%m_%d-%H%M {}".format(backtest_result.backtest_name))
        self._report_dir = path.join("backtesting", sub_dir_name)

        self._init_live_progress_chart(backtest_result)
        self._csv_file, self._csv_writer = self._init_transactions_log_csv_file()

        self._eod_update_ctr = 0

    def end_of_trading_update(self, _: datetime = None):
        """
        Saves the results of the backtest
        """
        portfolio_tms = self.backtest_result.portfolio.portfolio_eod_series()
        portfolio_tms.name = self.backtest_result.backtest_name

        self._issue_tearsheet(portfolio_tms)
        self._issue_portfolio_analysis_sheet(self.backtest_result)
        self._issue_trade_analysis_sheet()
        self._issue_factor_sector_exposure_sheet()
        self._issue_daily_portfolio_value_file(portfolio_tms)
        self._issue_signal_log()
        self._issue_config_log()
        self._print_stats_to_console(portfolio_tms)

        self._close_files()

    def end_of_day_update(self, _: datetime = None):
        """
        Update real time line chart with current backtest progress every fixed number of days
        """
        self._eod_update_ctr += 1
        if self._eod_update_ctr % self._monitor_settings.live_backtest_chart_refresh_frequency == 0:
            self._live_chart_update()

    def real_time_update(self, _: datetime = None):
        """
        This method will not be used by the historical backtest
        """
        pass

    def record_transaction(self, transaction: Transaction):
        """
        Save the transaction in backtest result (and in the file if set to do so)
        """
        self.backtest_result.transactions.append(transaction)
        self._save_transaction_to_file(transaction)

    @ErrorHandling.error_logging
    def _init_live_progress_chart(self, backtest_result: BacktestResult):
        if self._monitor_settings.display_live_backtest_progress:
            # Set up an empty chart that can be updated
            self._figure, self._ax = plt.subplots()
            self._figure.set_size_inches(12, 5)
            self._line, = self._ax.plot([], [])

            self._ax.set_autoscaley_on(True)

            end_date = backtest_result.end_date if backtest_result.end_date is not None else datetime.now()
            self._ax.set_xlim(backtest_result.start_date, end_date)
            self._ax.grid()
            self._ax.set_title("Progress of the backtest - {}".format(backtest_result.backtest_name))
            self._figure.autofmt_xdate(rotation=20)

    @ErrorHandling.error_logging
    def _init_transactions_log_csv_file(self) -> Tuple[Optional[TextIOWrapper], Optional[csv.writer]]:
        """
        Creates a new csv file for every backtest run, writes the header and returns the file handler and writer object
        """
        if self._monitor_settings.issue_transaction_log:
            output_dir = path.join(get_starting_dir_abs_path(), self._settings.output_directory, self._report_dir)
            if not path.exists(output_dir):
                makedirs(output_dir)

            csv_filename = "%Y_%m_%d-%H%M Transactions.csv"
            csv_filename = datetime.now().strftime(csv_filename)
            file_path = path.expanduser(path.join(output_dir, csv_filename))

            # Write new file header
            fieldnames = ["Timestamp", "Asset Name", "Contract symbol", "Security type", "Contract size", "Quantity",
                          "Price", "Commission"]

            file_handler = open(file_path, 'a', newline='')
            writer = csv.DictWriter(file_handler, fieldnames=fieldnames)
            writer.writeheader()
            csv_writer = csv.writer(file_handler)
            return file_handler, csv_writer
        return None, None

    @ErrorHandling.error_logging
    def _close_files(self):
        if self._csv_file is not None:
            self._csv_file.close()

    @ErrorHandling.error_logging
    def _save_transaction_to_file(self, transaction: Transaction):
        """
        Append all details about the Transaction to the CSV trade log.
        """
        if self._monitor_settings.issue_transaction_log and self._csv_writer is not None:
            self._csv_writer.writerow([
                transaction.transaction_fill_time,
                transaction.ticker.name,
                transaction.ticker.ticker,
                transaction.ticker.security_type.value,
                transaction.ticker.point_value,
                transaction.quantity,
                transaction.price,
                transaction.commission
            ])

    @ErrorHandling.error_logging
    def _issue_daily_portfolio_value_file(self, portfolio_tms):
        if self._monitor_settings.issue_daily_portfolio_value_file:
            xlsx_filename = "%Y_%m_%d-%H%M Timeseries.xlsx"
            xlsx_filename = datetime.now().strftime(xlsx_filename)
            file_path = path.join(self._report_dir, xlsx_filename)
            # export portfolio tms
            self._excel_exporter.export_container(portfolio_tms, file_path,
                                                  starting_cell='A1', include_column_names=True)
            # export leverage tms
            leverage_tms = self.backtest_result.portfolio.leverage_series()
            self._excel_exporter.export_container(leverage_tms, file_path, sheet_name="Leverage",
                                                  starting_cell='A1', include_column_names=True)
            # export benchmark tms if provided
            if self.benchmark_tms is not None:
                self._excel_exporter.export_container(self.benchmark_tms, file_path,
                                                      starting_cell='C1', include_column_names=True)

    @ErrorHandling.error_logging
    def _issue_portfolio_analysis_sheet(self, backtest_result: BacktestResult):
        if self._monitor_settings.issue_portfolio_analysis_sheet:
            pnl_charts_flag = self._monitor_settings.generate_pnl_chart_per_ticker_in_portfolio_analysis
            portfolio_trading_sheet = PortfolioAnalysisSheet(self._settings, self._pdf_exporter, backtest_result,
                                                             title=backtest_result.backtest_name,
                                                             generate_pnl_chart_per_ticker=pnl_charts_flag)
            portfolio_trading_sheet.build_document()
            portfolio_trading_sheet.save(self._report_dir)

    @ErrorHandling.error_logging
    def _issue_tearsheet(self, portfolio_tms):
        if self._monitor_settings.issue_tearsheet:
            if self.benchmark_tms is None:
                tearsheet = TearsheetWithoutBenchmark(
                    self._settings, self._pdf_exporter, portfolio_tms, title=portfolio_tms.name)
            else:
                tearsheet = TearsheetWithBenchmark(
                    self._settings, self._pdf_exporter, portfolio_tms, self.benchmark_tms, title=portfolio_tms.name)

            tearsheet.build_document()
            tearsheet.save(self._report_dir)

    @ErrorHandling.error_logging
    def _print_stats_to_console(self, portfolio_tms):
        if self._monitor_settings.print_stats_to_console:
            if self.benchmark_tms is None:
                ta = TimeseriesAnalysis(portfolio_tms, frequency=Frequency.DAILY)
                print(TimeseriesAnalysis.values_in_table(ta))
            else:
                ta_portfolio = TimeseriesAnalysis(portfolio_tms, frequency=Frequency.DAILY)
                ta_benchmark = TimeseriesAnalysis(self.benchmark_tms, frequency=Frequency.DAILY)
                print(TimeseriesAnalysis.values_in_table([ta_portfolio, ta_benchmark]))

    @ErrorHandling.error_logging
    def _issue_trade_analysis_sheet(self):
        """
        Create TradeAnalysisSheet and write all the Trades into an Excel file.
        Issues a report with R multiply if initial risk is specified, otherwise returns of trades are expressed in %
        """
        if self._monitor_settings.issue_trade_analysis_sheet:
            trades_generator = TradesGenerator()
            portfolio_eod_series = self.backtest_result.portfolio.portfolio_eod_series()
            closed_positions = self.backtest_result.portfolio.closed_positions()
            trades_list = trades_generator.create_trades_from_backtest_positions(closed_positions, portfolio_eod_series)

            if len(trades_list) > 0:
                nr_of_assets_traded = len(set(t.ticker.name for t in trades_list))
                start_date = self.backtest_result.start_date or portfolio_eod_series.index[0]
                end_date = self.backtest_result.end_date or datetime.now()

                trades_analysis_sheet = TradeAnalysisSheet(self._settings, self._pdf_exporter,
                                                           nr_of_assets_traded=nr_of_assets_traded,
                                                           trades=trades_list,
                                                           start_date=start_date,
                                                           end_date=end_date,
                                                           initial_risk=self.backtest_result.initial_risk,
                                                           title="Trades analysis sheet")
                trades_analysis_sheet.build_document()
                trades_analysis_sheet.save(self._report_dir)
            else:
                self.logger.info("No trades generated during the backtest - TradeAnalysisSheet will not be generated.")

    @ErrorHandling.error_logging
    def _issue_factor_sector_exposure_sheet(self):
        if self._monitor_settings.exposure_settings is not None:
            exposure_generator = ExposureGenerator(self._settings, self._monitor_settings.exposure_settings.data_provider)

            # setting ExposureGenerator parameters
            exposure_generator.set_positions_history(self.backtest_result.portfolio.positions_history())
            exposure_generator.set_portfolio_nav_history(self.backtest_result.portfolio.portfolio_eod_series())
            exposure_generator.set_sector_exposure_tickers(self._monitor_settings.exposure_settings.sector_exposure_tickers)
            exposure_generator.set_factor_exposure_tickers(self._monitor_settings.exposure_settings.factor_exposure_tickers)

            # getting sector exposure
            sector_df = exposure_generator.get_sector_exposure()

            # getting factor exposure
            factor_df = exposure_generator.get_factor_exposure()

            exposure_sheet = ExposureSheet(self._settings, self._pdf_exporter, self.backtest_result.backtest_name)

            # setting data for charts
            exposure_sheet.set_sector_data(sector_df)
            exposure_sheet.set_factor_data(factor_df)

            exposure_sheet.build_document()
            exposure_sheet.save(self._report_dir)
        else:
            self.logger.info("DataProvider for Exposure Sheet was not set up. ExposureSheet will not be generated.")

    @ErrorHandling.error_logging
    def _issue_signal_log(self):
        if self._monitor_settings.issue_signal_log:
            signals_df = self._signals_register.get_signals()
            xlsx_filename = "%Y_%m_%d-%H%M Signals.xlsx"
            xlsx_filename = datetime.now().strftime(xlsx_filename)
            file_path = path.join(self._report_dir, xlsx_filename)

            # Export the signals only if the data frame is not empty
            if not signals_df.empty:
                sheet_names_to_functions = {
                    "Tickers": lambda s: s.symbol if isinstance(s, Signal) else s,
                    "Suggested exposure": lambda s: s.suggested_exposure.value if isinstance(s, Signal) else s,
                    "Confidence": lambda s: s.confidence if isinstance(s, Signal) else s,
                    "Expected move": lambda s: s.expected_move if isinstance(s, Signal) else s,
                    "Fraction at risk": lambda s: s.fraction_at_risk if isinstance(s, Signal) else s
                }

                for sheet_name, fun in sheet_names_to_functions.items():
                    df = signals_df.applymap(fun)
                    self._excel_exporter.export_container(df, file_path, sheet_name=sheet_name,
                                                          starting_cell='A1', include_column_names=True)

    @ErrorHandling.error_logging
    def _live_chart_update(self):
        if self._monitor_settings.display_live_backtest_progress:
            portfolio_tms = self.backtest_result.portfolio.portfolio_eod_series()
            self._ax.grid()

            # Set the data on x and y
            self._line.set_xdata(portfolio_tms.index)
            self._line.set_ydata(portfolio_tms.values)

            # Need both of these in order to rescale
            self._ax.relim()
            self._ax.autoscale_view()

            # We need to draw and flush
            self._figure.canvas.draw()
            self._figure.canvas.flush_events()

            self._ax.grid()  # we need two grid() calls in order to keep the grid on the chart

    @ErrorHandling.error_logging
    def _issue_config_log(self):
        if self._monitor_settings.issue_config_log:
            filename = "%Y_%m_%d-%H%M Config.yml"
            filename = datetime.now().strftime(filename)
            output_dir = path.join(get_starting_dir_abs_path(), self._settings.output_directory, self._report_dir)
            file_path = path.join(output_dir, filename)

            with open(file_path, "w") as file:
                ConfigExporter.print_config(file)
