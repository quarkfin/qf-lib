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

import datetime
import io
from itertools import islice
from os.path import exists
from typing import Union

import numpy as np
from openpyxl import load_workbook

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.excel.helpers import get_bounding_box


class ExcelImporter:
    """
    Class used for importing Series and DataFrames from the Excel files.
    """

    def __init__(self):
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def import_cell(
            self, file_path: str, cell_address: str, sheet_name: str = None) -> Union[int, float, str]:
        """
        Imports a container of given type (e.g. Series/DataFrame) from the Excel file of a given name.

        Parameters
        ----------
        file_path
            path to the file containing the data to be imported
        cell_address
            address of the cell that you want to get (e.g. 'A1')
        sheet_name
            the name of the sheet from which the container should be imported. If no name is given, the active worksheet
            is used.

        Returns
        -------
        container
            object containing the imported value
        """
        self.logger.info("Started importing data from {}".format(file_path))
        work_book = self._get_work_book(file_path)
        work_sheet = self._get_work_sheet(work_book, sheet_name)
        result = work_sheet[cell_address]
        work_book.close()
        return result.value

    def import_container(
            self, file_path: str, starting_cell: str, ending_cell: str, container_type: type = None,
            sheet_name: str = None, include_index: bool = True, include_column_names: bool = False) \
            -> Union[QFSeries, QFDataFrame]:
        """
        Imports a container of given type (e.g. Series/DataFrame) from the Excel file of a given name.

        Parameters
        ----------
        file_path:
            path to the file containing the data to be imported
        starting_cell
            top left corner of the imported container (e.g. A1)
        ending_cell
            bottom right corner of the imported container (e.g. B10)
        container_type
            type of the container to import. If none is given, then it is inferred from the bounding box
            (Series, if there is a single column, DataFrame for multiple columns). Other custom series and dataframe
            types that extend the Series and DataFrame types can also be used, this includes QFSeries and QFDataFrame.
        sheet_name
            the name of the sheet from which the container should be imported. If no name is given, the active worksheet
            is used.
        include_index
            if True than it is assumed that index is placed in the first column while values are starting from the 2nd
            column
        include_column_names
            determines whether the first row in the specified container contains the column names.

        Returns
        -------
        container
            object containing the imported data
        """
        self.logger.info("Started importing data from {}".format(file_path))
        start_time = datetime.datetime.now()

        work_book = self._get_work_book(file_path)
        work_sheet = self._get_work_sheet(work_book, sheet_name)

        bounding_box = get_bounding_box(starting_cell, ending_cell)

        nr_of_non_index_columns = bounding_box.ending_column - bounding_box.starting_column + 1
        if include_index:
            nr_of_non_index_columns -= 1  # one column for index, thus -1

        if container_type is None:
            container_type = self._infer_container_type(nr_of_non_index_columns)

        if not self._is_correct_containers_type(container_type, nr_of_non_index_columns):
            raise ValueError("Incorrect container's type")
        container = self._load_container(work_sheet, container_type, bounding_box, include_index, include_column_names)

        end_time = datetime.datetime.now()
        execution_time = end_time - start_time
        self.logger.info("Ended importing data from {} after {}".format(file_path, execution_time))

        work_book.close()
        return container.squeeze()

    def _get_work_book(self, file_path):
        assert exists(file_path)
        with open(file_path, "rb") as f:
            in_memory_file = io.BytesIO(f.read())
        work_book = load_workbook(in_memory_file, read_only=True, data_only=True)
        return work_book

    def _get_work_sheet(self, work_book, sheet_name):
        if sheet_name is None:
            work_sheet = work_book.active
        else:
            work_sheet = work_book[sheet_name]

        return work_sheet

    def _infer_container_type(self, nr_of_non_index_columns):
        if nr_of_non_index_columns <= 0:
            raise ValueError("Ending column must have higher index than starting column and if the include_index==True,"
                             "then there must be at least two columns in the bounding box")

        container_type = None
        if nr_of_non_index_columns > 1:
            container_type = QFDataFrame
        elif nr_of_non_index_columns == 1:
            container_type = QFSeries

        return container_type

    def _is_correct_containers_type(self, container_type, nr_of_non_index_columns):
        if nr_of_non_index_columns > 1:
            correct_container_type = issubclass(container_type, QFDataFrame)
        else:
            correct_container_type = issubclass(container_type, QFSeries)

        return correct_container_type

    def _load_container(self, work_sheet, container_type, bounding_box, include_index, include_column_names):
        container = None
        if issubclass(container_type, QFSeries):
            container = self._load_series(work_sheet, container_type, bounding_box, include_index, include_column_names)
        elif issubclass(container_type, QFDataFrame):
            container = self._load_dataframe(
                work_sheet, container_type, bounding_box, include_index, include_column_names)

        return container

    def _load_series(self, work_sheet, container_type, bounding_box, include_index, include_column_names):
        starting_column = bounding_box.starting_column
        starting_row = bounding_box.starting_row
        ending_row = bounding_box.ending_row

        if include_column_names:
            # Ignore the column names in this case.
            starting_row += 1

        index = None
        values_column = starting_column
        if include_index:
            index = self._load_column(work_sheet, starting_row, ending_row, starting_column)
            values_column += 1

        values = self._load_column(work_sheet, starting_row, ending_row, values_column)

        return container_type(data=values, index=index)

    def _load_dataframe(self, work_sheet, container_type, bounding_box, include_index, include_column_names):
        starting_column = bounding_box.starting_column
        starting_row = bounding_box.starting_row
        ending_column = bounding_box.ending_column
        ending_row = bounding_box.ending_row

        # Read the column names at the top of the dataframe.
        column_names = None
        if include_column_names:
            column_names = self._load_row(work_sheet, starting_row)
            column_names = column_names[starting_column - 1:ending_column]
            starting_row += 1

        index = None
        if include_index:
            index = self._load_column(work_sheet, starting_row, ending_row, starting_column)
            if column_names is not None:
                column_names = column_names[1:]
            starting_column += 1

        rows_values = []

        for row in islice(work_sheet.rows, starting_row - 1, ending_row):
            row_values = [cell.value for cell in islice(row, starting_column - 1, ending_column)]
            rows_values.append(row_values)

        values = np.array(rows_values)

        return container_type(index=index, data=values, columns=column_names)

    def _load_column(self, work_sheet, starting_row, ending_row, column_nr):
        values = []

        row_nr = 1
        for row in work_sheet.rows:
            if starting_row <= row_nr <= ending_row:
                col_nr = 1
                for cell in row:
                    if col_nr == column_nr:
                        values.append(cell.value)
                    col_nr += 1

            row_nr += 1

        return values

    def _load_row(self, work_sheet, row_index):
        for i, row in enumerate(work_sheet.rows):
            if i == row_index - 1:
                return [cell.value for cell in row]

        return None
