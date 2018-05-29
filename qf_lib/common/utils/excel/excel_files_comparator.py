import xlrd


class ExcelFilesComparator(object):
    def assert_the_same(self, file_path_1, file_path_2):
        """
        Compares two excel files. Checks if they have the same sheets and the same content (values only, not styles).
        If the files are not the same the AssertionError will be raised.

        Parameters
        ----------
        file_path_1: str
            path to the first file
        file_path_2: str
            path to the second file
        """
        work_book1 = xlrd.open_workbook(file_path_1)
        work_book2 = xlrd.open_workbook(file_path_2)

        sheets_count = work_book1.nsheets
        assert work_book2.nsheets == sheets_count,\
            "Different number of worksheets in workbooks: {}, {}".format(sheets_count, work_book2.nsheets)

        for sheet_nr in range(sheets_count):
            sheet1 = work_book1.sheet_by_index(sheet_nr)
            sheet2 = work_book2.sheet_by_index(sheet_nr)

            self.assert_sheets_the_same(sheet1, sheet2, sheet_nr)

    def assert_sheets_the_same(self, sheet1, sheet2, sheet_nr):
        rows_count = sheet1.nrows
        columns_count = sheet1.ncols

        assert sheet2.nrows == rows_count,\
            "Different number of rows for sheet nr: {}: {} and {}".format(sheet_nr, rows_count, sheet2.nrows)

        assert sheet2.ncols == columns_count,\
            "Different number of columns for sheet nr: {}: {} and {}".format(sheet_nr, columns_count, sheet2.ncols)

        for row_nr in range(rows_count):
            for column_nr in range(columns_count):
                cell_value = sheet1.cell(row_nr, column_nr).value
                another_cell_value = sheet2.cell(row_nr, column_nr).value

                assert cell_value == another_cell_value, \
                    "Different cell's value in sheet nr: {}, for row_nr: {}, column_nr: {}, values: {}/{}".format(
                        sheet_nr, row_nr, column_nr, cell_value, another_cell_value
                    )
