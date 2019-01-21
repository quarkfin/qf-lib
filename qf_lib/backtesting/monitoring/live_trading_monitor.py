# it is important to import the matplotlib first and then switch the interactive/dynamic mode on.
import csv
from datetime import datetime
from io import TextIOWrapper
from os import path, makedirs

from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class LiveTradingMonitor(AbstractMonitor):
    """
    This Monitor will be used to monitor live trading activities
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, excel_exporter: ExcelExporter):
        self._settings = settings
        self._pdf_exporter = pdf_exporter
        self._excel_exporter = excel_exporter
        self._report_dir = "live_trading"
        self._csv_file = self._init_csv_file("Live_Trading_Trades")
        self._csv_writer = csv.writer(self._csv_file)

    def end_of_trading_update(self, _: datetime = None):
        """
        Close the CSV file
        """
        self._close_csv_file()

    def end_of_day_update(self, timestamp: datetime = None):
        """
        Do nothing
        """
        pass

    def real_time_update(self, timestamp: datetime = None):
        """
        Do nothing
        """
        pass

    def record_transaction(self, transaction: Transaction):
        """
        Print the trade to the CSV file
        """
        self._csv_writer.writerow([
            transaction.time,
            transaction.contract.symbol,
            transaction.quantity,
            transaction.price,
            transaction.commission
        ])

    def _init_csv_file(self, file_name_template: str) -> TextIOWrapper:
        """
        Creates a new csv file for every backtest run, writes the header and returns the path to the file.
        """
        output_dir = path.join(get_starting_dir_abs_path(), self._settings.output_directory, self._report_dir)
        if not path.exists(output_dir):
            makedirs(output_dir)

        csv_filename = "{}.csv".format(file_name_template)
        file_path = path.expanduser(path.join(output_dir, csv_filename))

        # Write new file header
        fieldnames = ["Timestamp", "Contract", "Quantity", "Price", "Commission"]

        if path.exists(file_path):
            file_handler = open(file_path, 'a', newline='')
        else:
            file_handler = open(file_path, 'a', newline='')
            # add header if file is just created
            writer = csv.DictWriter(file_handler, fieldnames=fieldnames)
            writer.writeheader()

        return file_handler

    def _close_csv_file(self):
        if self._csv_file is not None:  # close the csv file
            self._csv_file.close()
