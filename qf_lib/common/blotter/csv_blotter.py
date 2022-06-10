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
from os import path, makedirs
from typing import List, Tuple, TextIO

from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.blotter.blotter import Blotter
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class CSVBlotter(Blotter):
    """
    Blotter writing transactions to a CSV File
    """

    def __init__(self, csv_file_path: str):
        self.file_path = csv_file_path
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.file_handler, self.csv_writer = self._init_csv_file()

    def save_transaction(self, transaction: Transaction):
        """
        Append all details about the Transaction to the CSV trade log.
        """
        if transaction is not None:
            self.csv_writer.writerow(transaction.get_row())

    def get_transactions(self, from_date: datetime = None, to_date: datetime = None) -> List[Transaction]:
        raise NotImplementedError()

    def _init_csv_file(self) -> Tuple[TextIO, csv.writer]:
        output_dir = path.dirname(self.file_path)
        if not path.exists(output_dir):
            self.logger.info(f'directory {output_dir} does not exist, creating directory...')
            makedirs(output_dir)

        if not path.exists(self.file_path):  # write header
            file_handler = open(self.file_path, 'a+', newline='')
            csv.DictWriter(file_handler, fieldnames=Transaction.get_header()).writeheader()
        else:
            file_handler = open(self.file_path, 'a+', newline='')

        # create writer and return
        csv_writer = csv.writer(file_handler)
        return file_handler, csv_writer

    def close_file(self):
        if self.file_handler is not None:
            self.file_handler.close()
