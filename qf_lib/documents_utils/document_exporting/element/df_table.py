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
from itertools import groupby
from typing import Sequence, Optional, Union, Dict, Any

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element
from qf_lib.documents_utils.document_exporting import templates


class DFTable(Element):
    def __init__(self, data: QFDataFrame = None, columns: Sequence[str] = None, css_classes: Union[str, Sequence[str]] =
                 "table", title: str = "", grid_proportion: GridProportion = GridProportion.Eight):
        super().__init__(grid_proportion)

        self.model = ModelController(data=data, index=data.index,
                                     columns=columns if columns is not None else data.columns)
        assert len(set(self.model.data.columns)) == len(self.model.data.columns), "Duplicated name columns are not allowed"

        # Set the initial Table css classes
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.table_styles.add_css_class(css_classes)

        self.title = title

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the underlying table element as HTML.
        """
        env = templates.environment
        template = env.get_template("df_table.html")

        # Support merging column cells using colspan in case of MultiIndex
        flat_index = self.columns.to_flat_index() if self.columns.nlevels > 1 else [(el, ) for el in self.columns]

        # The following list consist of a number of lists per each multi index level, each of which contains information
        # about the number of occurrences of each column, e.g. MultiIndex([('A', 'X'), ('A', 'Y'), ('B', 'Y')]) would be
        # mapped onto [[('A', 2), ('B', 1)], [('X', 1), ('Y', 1), ('Y', 1)]] as first level contains of A (colspan=2)
        # and B (colspan=1) and the second one - X (colspan=1) and two times Y (colspan=1) (we don't merge those two
        # cells as one belongs to 'A' and the other to 'B')
        columns_to_occurrences = [
            [(x[level], len(list(y))) for x, y in groupby(flat_index, lambda tup: tup[:level+1])]
            for level in range(self.columns.nlevels)
        ]

        return template.render(css_class=self.model.table_styles.classes(), table=self, columns=columns_to_occurrences)

    @property
    def columns(self):
        return self.model.data.columns

    def set_columns(self, column_names: Sequence[str]):
        self.model.data.columns = column_names

    def append(self, data: Union[QFDataFrame, QFSeries, Dict], ignore_index=False, verify_integrity=False, sort=None):
        self.model.data = self.model.data.append(data, ignore_index, verify_integrity, sort)

    def sort_by_column(self, columns: Union[str, Sequence[str]], css_class=("sorted-by-column",), ascending=True):
        # Sort by the given columns
        self.model.data.sort_values(inplace=True, by=columns, ascending=ascending)
        # Highlight the columns by adding a certain css class to them
        self.model.add_columns_classes(columns, css_class)

    def add_table_classes(self, css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.table_styles.add_css_class(css_classes)

    def remove_table_classes(self, css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.table_styles.remove_css_class(css_classes)

    def add_columns_styles(self, columns: Union[str, Sequence[str]], css_styles: Dict[str, str]):
        self.model.add_columns_styles(columns, css_styles)

    def add_columns_classes(self, columns: Union[str, Sequence[str]], css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.add_columns_classes(columns, css_classes)

    def remove_columns_styles(self, columns: Union[str, Sequence[str]],
                              css_styles: Union[Dict[str, str], Sequence[str]]):
        self.model.remove_columns_styles(columns, css_styles)

    def remove_columns_classes(self, columns: Union[str, Sequence[str]], css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.remove_columns_classes(columns, css_classes)

    def add_rows_styles(self, loc_indexer: Union[Any, Sequence[Any]], css_styles: Dict[str, str]):
        self.model.add_rows_styles(loc_indexer, css_styles)

    def add_rows_classes(self, loc_indexer: Union[Any, Sequence[Any]], css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.add_rows_classes(loc_indexer, css_classes)

    def remove_rows_styles(self, loc_indexer: Union[Any, Sequence[Any]], styles: Union[Dict[str, str], Sequence[str]]):
        self.model.remove_rows_styles(loc_indexer, styles)

    def remove_rows_classes(self, loc_indexer: Union[Any, Sequence[Any]], css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.remove_rows_classes(loc_indexer, css_classes)

    def add_cells_styles(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                         css_styles: Dict[str, str]):
        self.model.add_cells_styles(columns, rows, css_styles)

    def add_cells_classes(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                          css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.add_cells_classes(columns, rows, css_classes)

    def remove_cells_styles(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                            styles: Union[Dict[str, str], Sequence[str]]):
        self.model.remove_cells_styles(columns, rows, styles)

    def remove_cells_classes(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                             css_classes: Union[str, Sequence[str]]):
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.remove_cells_classes(columns, rows, css_classes)


class ModelController:
    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False):

        self.logger = qf_logger.getChild(self.__class__.__name__)

        # Data Frame containing the table data
        self.data = QFDataFrame(data, index, columns, dtype, copy)

        # Dictionary containing a mapping from column names onto ColumnStyles
        self._columns_styles = {
            column_name: self.ColumnStyle(column_name)
            for column_name in self.data.columns.tolist()
        }

        # Series containing the styles for each of the rows
        self._rows_styles = QFSeries(data=[
            self.RowStyle(loc) for loc in self.data.index
        ], index=self.data.index)

        # Data Frame containing styles for all cells in the table, based upon columns_styles and rows_styles
        self._styles = QFDataFrame(data={
            column_name: [
                self.CellStyle(row_style, column_style) for row_style in self.rows_styles
            ] for column_name, column_style in self.columns_styles.items()
        }, index=self.data.index, columns=self.data.columns)

        self.table_styles = self.Style()

    def add_columns_styles(self, columns: Union[str, Sequence[str]], styles_dict: Dict[str, str]):
        if not isinstance(columns, list):
            columns = [columns]

        for column_name in columns:
            self.columns_styles[column_name].add_styles(styles_dict)

    def add_columns_classes(self, columns: Union[str, Sequence[str]], css_classes: Sequence[str]):
        if not isinstance(columns, list):
            columns = [columns]

        for column_name in columns:
            self.columns_styles[column_name].add_css_class(css_classes)

    def remove_columns_classes(self, columns: Union[str, Sequence[str]], css_classes: Sequence[str]):
        if not isinstance(columns, list):
            columns = [columns]

        for column_name in columns:
            self.columns_styles[column_name].remove_css_class(css_classes)

    def remove_columns_styles(self, columns: Union[str, Sequence[str]], styles: Union[Dict[str, str], Sequence[str]]):
        if not isinstance(columns, list):
            columns = [columns]

        for column_name in columns:
            self.columns_styles[column_name].remove_styles(styles)

    def add_rows_styles(self, loc_indexer: Union[Any, Sequence[Any]], styles_dict: Dict[str, str]):
        for row in self.rows_styles.loc[loc_indexer]:
            row.add_styles(styles_dict)

    def add_rows_classes(self, loc_indexer: Union[Any, Sequence[Any]], css_classes: Sequence[str]):
        for row in self.rows_styles.loc[loc_indexer]:
            row.add_css_class(css_classes)

    def remove_rows_styles(self, loc_indexer: Union[Any, Sequence[Any]], styles: Union[Dict[str, str], Sequence[str]]):
        for row in self.rows_styles.loc[loc_indexer]:
            row.remove_styles(styles)

    def remove_rows_classes(self, loc_indexer: Union[Any, Sequence[Any]], css_classes: Sequence[str]):
        for row in self.rows_styles.loc[loc_indexer]:
            row.remove_css_class(css_classes)

    def add_cells_styles(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                         css_styles: Dict[str, str]):
        if not isinstance(columns, list):
            columns = [columns]

        if not isinstance(rows, list):
            rows = [rows]

        for column_name in columns:
            for row in rows:
                self.styles.loc[row, column_name].add_styles(css_styles)

    def add_cells_classes(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                          css_classes: Sequence[str]):
        if not isinstance(columns, list):
            columns = [columns]

        if not isinstance(rows, list):
            rows = [rows]

        for column_name in columns:
            for row in rows:
                self.styles.loc[row, column_name].add_css_class(css_classes)

    def remove_cells_styles(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                            styles: Union[Dict[str, str], Sequence[str]]):
        if not isinstance(columns, list):
            columns = [columns]

        if not isinstance(rows, list):
            rows = [rows]

        for column_name in columns:
            for row in rows:
                self.styles.loc[row, column_name].remove_styles(styles)

    def remove_cells_classes(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                             css_classes: Sequence[str]):
        if not isinstance(columns, list):
            columns = [columns]

        if not isinstance(rows, list):
            rows = [rows]

        for column_name in columns:
            for row in rows:
                self.styles.loc[row, column_name].remove_css_class(css_classes)

    def iterrows(self):
        return zip(self.data.iterrows(), self.styles.iterrows())

    @property
    def styles(self):

        def get_cell(row_style, column_style, column_name):
            try:
                row_indexer = row_style.label
                column_indexer = column_name
                return self._styles.loc[row_indexer, column_indexer]
            except KeyError:
                return self.CellStyle(row_style, column_style)

        self._styles = QFDataFrame(data={
            column_name: [
                get_cell(row_style, column_style, column_name) for row_style in self.rows_styles
            ] for column_name, column_style in self.columns_styles.items()
        }, index=self.data.index, columns=self.data.columns)
        return self._styles

    @property
    def columns_styles(self):
        if set(self._columns_styles.keys()) != set(self.data.columns):
            # Delete the unnecessary columns styles
            self._columns_styles = {column_name: column_style for column_name, column_style in
                                    self._columns_styles.items()
                                    if column_name in self.data.columns}
            # Add columns styles, which do not exist yet
            existing_columns = [column_name for column_name in self._columns_styles.keys()]
            self._columns_styles.update({
                column_name: self.ColumnStyle(column_name) for column_name in self.data.columns.tolist()
                if column_name not in existing_columns
            })

        return self._columns_styles

    @property
    def rows_styles(self):
        if not self._rows_styles.index.equals(self.data.index):
            # Delete the unnecessary rows styles
            indices_to_delete = [index for index in self._rows_styles.index if index not in self.data.index]
            self._rows_styles.drop(indices_to_delete, inplace=True)

            # Add rows styles, which do not exist yet
            new_indices = [index for index in self.data.index if index not in self._rows_styles.index]
            new_row_styles = QFSeries([
                self.RowStyle(loc) for loc in new_indices
            ], index=new_indices)

            self._rows_styles = self._rows_styles.append(new_row_styles, ignore_index=False)

        return self._rows_styles

    class Style:
        def __init__(self, style: Dict[str, str] = None, css_class: str = None):
            self.style = style if style is not None else dict()
            self.css_class = css_class.split() if css_class is not None else []
            self.logger = qf_logger.getChild(self.__class__.__name__)

        def add_css_class(self, css_classes: Sequence[str]):
            self.css_class.extend(css_classes)

        def remove_css_class(self, css_classes: Sequence[str]):
            for class_name in css_classes:
                try:
                    self.css_class.remove(class_name)
                except ValueError:
                    self.logger.warning("The css class {} can not be removed, as it does not exist".format(class_name))

        def add_styles(self, styles_dict: Dict[str, str]):
            styles_dict = {key.replace(" ", ""): value.replace(" ", "") for key, value in styles_dict.items()}
            self.style.update(styles_dict)

        def remove_styles(self, styles: Union[Dict[str, str], Sequence[str]]):
            properties = styles.keys() if type(styles) is dict else styles
            for property_name in properties:
                try:
                    del self.style[property_name]
                except KeyError:
                    self.logger.warning("The css style for proptyety {} can not be removed, as it does not exist".
                                        format(property_name))

        def styles(self):
            # The function merges into string all styles. This string may be further used as the css styles attributes
            # value. No spaces between attributes and their values are allowed.
            def merge_styles(styles_dict: Dict[str, str]) -> str:
                return "".join(['%s:%s;' % (key, value) for key, value in styles_dict.items()])

            styles = merge_styles(self.style)
            styles = '""' if len(styles) == 0 else styles

            return styles

        def classes(self):
            def merge_classes(css_classes_list: Sequence[str]) -> str:
                return " ".join(css_classes_list)

            css_classes = merge_classes(self.css_class)
            return css_classes

    class ColumnStyle(Style):
        def __init__(self, column_name: str, style: Dict[str, str] = None, css_class: str = None):
            super().__init__(style, css_class)
            self.column_name = column_name

    class RowStyle(Style):
        def __init__(self, label: Any, style: Dict[str, str] = None, css_class: str = None):
            super().__init__(style, css_class)
            self.label = label

    class CellStyle(Style):
        def __init__(self, row_style, column_style, style: Dict[str, str] = None, css_class: str = None):
            super().__init__(style, css_class)
            self.row_style = row_style
            self.column_style = column_style

        def styles(self):
            # The function merges into string all styles, corresponding to the row, column and cell.
            styles = super().styles()

            styles = self.row_style.styles() + self.column_style.styles() + styles
            styles = styles.replace('""', '')
            styles = '""' if len(styles) == 0 else styles

            return styles

        def classes(self):
            # The function merges into string all styles, corresponding to the row, column and cell. This string may be
            # further used as the css class attribute value
            classes = super().classes()

            css_classes = self.row_style.classes() + self.column_style.classes() + classes
            css_classes = css_classes.replace('""', '')
            css_classes = '""' if len(css_classes) == 0 else css_classes

            return css_classes
