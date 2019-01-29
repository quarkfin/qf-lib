# it is important to import the matplotlib first and then switch the interactive/dynamic mode on.
import csv
from datetime import datetime
from io import TextIOWrapper
from os import path, makedirs
from typing import List

from pandas import Series

from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.publishers.email_publishing.email_publisher import EmailPublisher
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class LiveTradingMonitor(AbstractMonitor):
    """
    This Monitor will be used to monitor live trading activities
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter,
                 excel_exporter: ExcelExporter, email_publisher: EmailPublisher):
        self._settings = settings
        self._pdf_exporter = pdf_exporter
        self._excel_exporter = excel_exporter
        self._email_publisher = email_publisher
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
        Generates #todo: what does it generate?
         and sends it by email
        """
        attachments_paths = [
            self._export_test_file()
        ]

        self._publish_by_email(attachments_paths, timestamp)

    def _export_test_file(self):
        # todo: export an actual file here
        xlsx_filename = 'test_file.xlsx'
        relative_file_path = path.join(self._report_dir, "test", xlsx_filename)
        test_tms = Series(name='test_tms', index=[0, 1, 2], data=['a', 'b', 'c'])
        return self._excel_exporter.export_container(test_tms, relative_file_path, include_column_names=True)

    def _publish_by_email(self, attachments_dirs: List[str], timestamp):
        class User(object):
            def __init__(self, name, surname, email_address=None):
                self.name = name
                self.surname = surname
                if email_address:
                    self.email_address = email_address
                else:
                    self.email_address = name.lower() + '.' + surname.lower() + "@cern.ch"

        date_str = date_to_str(timestamp.date())
        template_path = 'live_trading_report.html'
        users = {
            User("Olga", "Kalinowska")
            # ,User("Jacek", "Witkowski")
        }
        for user in users:
            self._email_publisher.publish(
                mail_to=user.email_address,
                subject="Test Message " + date_str,
                template_path=template_path,
                attachments=attachments_dirs,
                context={'user': user, 'date': date_str}
            )

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
