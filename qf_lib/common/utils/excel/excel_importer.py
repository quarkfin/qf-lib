import datetime
import logging
from itertools import islice
from os.path import exists

import numpy as np
import pandas as pd
from openpyxl import load_workbook

from qf_lib.common.utils.excel.helpers import get_bounding_box


class ExcelImporter(object):
    """
    Class used for importing Series and DataFrames from the Excel files.
    """

    def import_container(self, file_path: str, starting_cell: str, ending_cell: str, container_type: type=None,
                         sheet_name: str=None, include_index: bool=True, include_column_names: bool=False):
        """
        Imports a container of given type (e.g. Series/DataFrame) from the Excel file of a given name.

        Parameters
        ----------
        file_path: str
            path to the file containing the data to be imported
        starting_cell: str
            top left corner of the imported container (e.g. A1)
        ending_cell: str
            bottom right corner of the imported container (e.g. B10)
        container_type: type, optional
            type of the container to import. If none is given, then it is inferred from the bounding box
            (Series, if there is a single column, DataFrame for multiple columns). Other custom series and dataframe
            types that extend the Series and DataFrame types can also be used, this includes QFSeries and QFDataFrame.
        sheet_name: str, optional
            the name of the sheet from which the container should be imported. If no name is given, the active worksheet
            is used.
        include_index: bool
            if True than it is assumed that index is placed in the first column while values are starting from the 2nd
            column
        include_column_names
            determines whether the first row in the specified container contains the column names.

        Returns
        -------
        container: Series or DataFrame
            object containing the imported data
        """
        logging.info("Started importing data from {}".format(file_path))
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
        logging.info("Ended importing data from {} after {}".format(file_path, execution_time))

        return container.squeeze()

    def _get_work_book(self, file_path):
        assert exists(file_path)
        work_book = load_workbook(file_path, read_only=True)
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
            container_type = pd.DataFrame
        elif nr_of_non_index_columns == 1:
            container_type = pd.Series

        return container_type

    def _is_correct_containers_type(self, container_type, nr_of_non_index_columns):
        if nr_of_non_index_columns > 1:
            correct_container_type = issubclass(container_type, pd.DataFrame)
        else:
            correct_container_type = issubclass(container_type, pd.Series)

        return correct_container_type

    def _load_container(self, work_sheet, container_type, bounding_box, include_index, include_column_names):
        container = None
        if issubclass(container_type, pd.Series):
            container = self._load_series(work_sheet, container_type, bounding_box, include_index, include_column_names)
        elif issubclass(container_type, pd.DataFrame):
            container = self._load_dataframe(work_sheet, container_type, bounding_box, include_index,
                                             include_column_names)

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

        for row in islice(work_sheet.rows, starting_row-1, ending_row):
            row_values = [cell.value for cell in islice(row, starting_column-1, ending_column)]
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
            if i == row_index-1:
                return [cell.value for cell in row]

        return None
