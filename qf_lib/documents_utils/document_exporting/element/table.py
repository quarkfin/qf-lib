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

import json
from html import escape
from typing import List, Any, Union, Optional, Dict

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class Table(Element):
    class Cell:
        def __init__(self, value: Any, format_string: str = "{}", css_class: str = "", escape_html: bool = True):
            """
            Creates a new cell. The class specifies how to format each cell in the table.

            Parameters
            ----------
            value
            format_string
                A string specifying how the value in this cell should be formatted.
            css_class
                The CSS class to apply to this cell.
            escape_html
                Whether the ``value`` should be escaped.
            """
            self.value = value
            self.format_string = format_string
            self.css_class = css_class
            self.escape_html = escape_html

        def __str__(self) -> str:
            string_value = self.format_string.format(self.value)
            if self.escape_html:
                string_value = escape(string_value, quote=True).replace("\n", "<br>")
                # escape spaces with "&nbsp" only at the beginning of the text. Escaping them between words leads
                # to issues
                string_value = self._escape_leading_spaces(string_value)

            return string_value

        def generate_dict(self) -> Dict[str, str]:
            return {"value": str(self), "css_class": self.css_class}

        def _escape_leading_spaces(self, s: str) -> str:
            result = []
            leading = True
            for c in s:
                if c == ' ' and leading:
                    result.append("&nbsp;")
                else:
                    leading = False
                    result.append(c)
            return "".join(result)

    class ColumnCell(Cell):
        def __init__(self, value: Any, format_string: str = "{}", css_class: str = "", column_css_class: str = ""):
            """
            Creates a new column cell, used in the table header.

            Parameters
            ----------
            value
            format_string
                A string specifying how the value in this cell should be formatted.
            css_class
                The CSS class to apply to this cell only.
            column_css_class
                The CSS class to apply to every cell in this column.
            """
            super().__init__(value, format_string, css_class)
            self.column_css_class = column_css_class

    def __init__(self, column_names: List[Union[str, ColumnCell]] = None, css_class: str = "table", title: str = "",
                 grid_proportion: GridProportion = GridProportion.Eight):
        """
        Constructs a new Table element.

        Parameters
        ----------
        column_names
            The column names to show in this table.
        css_class
            The css class to generate in the html for the <table> tag.
        """
        super().__init__(grid_proportion)
        self._column_cells = []
        if column_names is not None:
            self.set_column_names(column_names)
        self.rows = []
        self._css_class = css_class
        self.html_data = {}
        self.title = title

    def set_column_names(self, column_names: List[Union[str, ColumnCell]]) -> None:
        """
        Sets the table's column names. The list can consist of either strings or ColumnCells.
        """
        column_cells = []
        # Wrap each column in a cell.
        for column in column_names:
            if isinstance(column, self.ColumnCell):
                column_cells.append(column)
            else:
                column_cells.append(self.ColumnCell(column, "{}", css_class="right-align"))
        self._column_cells = column_cells

    def get_column_names(self) -> List[ColumnCell]:
        """
        Retrieves a list of column cells containing the column names in this table.
        """
        return self._column_cells

    def add_row(self, values: List[Any], css_class: str = "") -> None:
        """
        Adds a new row to the table. The ``values`` parameter must contain the same amount of elements as this
        table's columns count.

        The specified ``css_class`` will be applied to each cell.

        Parameters
        ----------
        values
            A list of values in this row, the values can be any type as long as it can be converted to a string.
        css_class
            The CSS class to apply to each cell in this row.
        """
        assert isinstance(self._column_cells, list)
        assert len(values) == len(self._column_cells)

        formatted_values = []
        # Format each of the values.
        for value in values:
            formatted_values.append(self._create_cell(value, css_class))
        self.rows.append(formatted_values)

    def insert_column(self, header: Union[str, ColumnCell], cells: List[Any], location: int, css_class: str = "") -> None:
        """
        Inserts a full column including a header and cells into the table at the specified location.

        The specified ``css_class`` will be applied to each cell except the header.

        Parameters
        ----------
        header
            The ColumnCell to place in the header of the table.
        cells
            A list of cells corresponding to each row that is currently in the table.
        location
            The index location of where this column should be inserted, starting from 0.
        css_class
            The CSS class to add to each Cell.
        """
        assert len(self.rows) == len(cells), "Number of cells must match number of rows in table"

        self._column_cells.insert(location, header)
        # Ensure that the inserted `header` is turned into a ColumnCell if it is not already one.
        self.set_column_names(self._column_cells)

        for i in range(0, len(cells)):
            self.rows[i].insert(location, self._create_cell(cells[i], css_class))

    def combine(self, table: "Table") -> "Table":
        """
        Combines the specified ``table`` into this table instance.

        The data in the first column of the other table has to match this instance's data.

        Parameters
        ----------
        table
            The table to combine into this table.

        Returns
        -------
        table
            A new combined table.
        """
        assert isinstance(self._column_cells, list)
        assert isinstance(table._column_cells, list)

        new_cols = [self._column_cells[0]]  # The first column is kept the same.
        # Copy the columns.
        for i in range(1, len(self._column_cells)):
            new_cols.append(self._column_cells[i])
        for i in range(1, len(table._column_cells)):
            new_cols.append(table._column_cells[i])

        # Copy the rows.
        new_rows = []
        for i in range(0, len(self.rows)):
            assert self.rows[i][0].value == table.rows[i][0].value, "The data in the first column must match."
            new_row = [self.rows[i][0]]  # The first column in each row is kept the same.
            # Copy each column from this table's row.
            for j in range(1, len(self._column_cells)):
                new_row.append(self.rows[i][j])
            # Copy each column from the other table's row.
            for j in range(1, len(table._column_cells)):
                new_row.append(table.rows[i][j])
            new_rows.append(new_row)

        result = Table(new_cols, css_class=self._css_class)
        result.rows = new_rows
        return result

    def create_diff_column(self, col_index1: int, col_index2: int):
        """
        Calculates the difference between column at index ``col_index1`` and ``col_index2``, then places this
        calculated difference in a new column.
        """
        assert isinstance(self._column_cells, list)
        self._column_cells.append("Diff ({}-{})".format(self._column_cells[col_index1],
                                                        self._column_cells[col_index2]))

        for row in self.rows:
            format_string = row[col_index1].format_string.replace("%", " pp")
            if isinstance(row[col_index1].value, (int, float)):
                row.append(self.Cell(row[col_index1].value - row[col_index2].value, format_string, "monospaced"))
            else:
                row.append(self.Cell("", format_string, "monospaced"))

    def create_fill_column(self, text: str = ""):
        """
        Adds a new column of cells at the end of the table, all with the same value specified by ``text``.
        """
        assert isinstance(self._column_cells, list)
        self._column_cells.append(text)

        for row in self.rows:
            row.append(self.Cell(text, "{}"))

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the underlying table element as HTML.
        """
        env = templates.environment

        template = env.get_template("table.html")
        return template.render(css_class=self._css_class, table=self)

    def generate_json(self) -> str:
        """
        Generates the underlying table element's rows and columns as JSON.
        """
        elem = {
            "column_names": self._column_cells,
            "rows": [[cell.generate_dict() for cell in row] for row in self.rows]
        }
        return json.dumps(elem)

    def _generate_data_attributes(self) -> str:
        result = ""
        for key, value in self.html_data.items():
            assert '"' not in key
            result += 'data-{}="{}" '.format(key, escape(value))
        return result

    def _create_cell(self, value: Any, css_class: str) -> Cell:
        if isinstance(value, float) or isinstance(value, int):
            return self.Cell(float(value), "{:7.2f}", "monospaced " + css_class)
        elif isinstance(value, self.Cell):
            value.css_class += " " + css_class
            return value
        else:
            return self.Cell(value, "{}", css_class)
