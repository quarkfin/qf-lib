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
from typing import Sequence, Optional, Union, Dict, Tuple, Any

from qf_lib.documents_utils.document_exporting.element.helpers.style import Style, ColumnStyle, RowStyle, CellStyle
from qf_lib.documents_utils.document_exporting.element.helpers.style_enums import DataType, StylingType
from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class DFTable(Element):
    def __init__(self, data: QFDataFrame = None, columns: Sequence[str] = None,
                 css_classes: Union[str, Sequence[str]] = "table", title: str = "",
                 grid_proportion: GridProportion = GridProportion.Eight, index_name: str = None):
        """
        Main method that modifies the css style and/or class of different elements in the ModelController
        Parameters
        ----------
        data: QFDataFrame
        columns: Sequence[str]
        css_classes: Union[str, Sequence[str]]
        title: str
        grid_proportion: GridProportion
        index_name: str
            If it is None, then the dftable won't show the index
            If it is any string (empty string included), the most upper level will take the name
        """
        super().__init__(grid_proportion)

        self.model = ModelController(data=data, index=data.index,
                                     columns=columns if columns is not None else data.columns)
        assert len(set(self.model.data.columns)) == len(
            self.model.data.columns), "Duplicated name columns are not allowed"

        # Set the initial Table css classes
        css_classes, _ = convert_to_list(css_classes, str)
        self.model.table_styles.add_css_class(css_classes)

        self.title = title
        self.index_name = index_name

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the underlying table element as HTML.
        """
        env = templates.environment
        template = env.get_template("df_table.html")

        # Support merging column cells using colspan in case of MultiIndex
        flat_index = self.columns.to_flat_index() if self.columns.nlevels > 1 else [(el,) for el in self.columns]

        # The following list consist of a number of lists per each multi index level, each of which contains information
        # about the number of occurrences of each column, e.g. MultiIndex([('A', 'X'), ('A', 'Y'), ('B', 'Y')]) would be
        # mapped onto [[('A', 2), ('B', 1)], [('X', 1), ('Y', 1), ('Y', 1)]] as first level contains of A (colspan=2)
        # and B (colspan=1) and the second one - X (colspan=1) and two times Y (colspan=1) (we don't merge those two
        # cells as one belongs to 'A' and the other to 'B')
        columns_to_occurrences = [
            [(x[level], len(list(y))) for x, y in groupby(flat_index, lambda tup: tup[:level + 1])]
            for level in range(self.columns.nlevels)
        ]

        if self.index_name is not None:
            index_levels = self.model.data.index.nlevels
            self.index_name = " " if len(self.index_name) == 0 else self.index_name

            columns_to_occurrences[0] = [(self.index_name, index_levels)] + columns_to_occurrences[0]
            for index, occurence in enumerate(columns_to_occurrences[1:]):
                columns_to_occurrences[index + 1] = [("", index_levels)] + occurence

        return template.render(css_class=self.model.table_styles.classes(), table=self,
                               columns=enumerate(columns_to_occurrences),
                               include_index=self.index_name is not None, index_styling=self.model.index_styling,
                               header_styling=self.model.header_styles)

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
        self.model.modify_data(columns, css_class, DataType.COLUMN, StylingType.CLASS)

    def add_table_classes(self, css_classes: Union[str, Sequence[str]]):
        self.model.modify_data(None, css_classes, DataType.TABLE, StylingType.CLASS)

    def remove_table_classes(self, css_classes: Union[str, Sequence[str]]):
        self.model.modify_data(None, css_classes, DataType.TABLE, StylingType.CLASS, False)

    def add_columns_styles(self, columns: Union[str, Sequence[str]], css_styles: Dict[str, str]):
        self.model.modify_data(columns, css_styles, DataType.COLUMN, StylingType.STYLE)

    def add_columns_classes(self, columns: Union[str, Sequence[str]], css_classes: Union[str, Sequence[str]]):
        self.model.modify_data(columns, css_classes, DataType.COLUMN, StylingType.CLASS)

    def remove_columns_styles(self, columns: Union[str, Sequence[str]],
                              css_styles: Union[Dict[str, str], Sequence[str]]):
        self.model.modify_data(columns, css_styles, DataType.COLUMN, StylingType.STYLE, False)

    def remove_columns_classes(self, columns: Union[str, Sequence[str]], css_classes: Union[str, Sequence[str]]):
        self.model.modify_data(columns, css_classes, DataType.COLUMN, StylingType.CLASS, False)

    def add_rows_styles(self, loc_indexer: Union[Any, Sequence[Any]], css_styles: Dict[str, str]):
        self.model.modify_data(loc_indexer, css_styles, DataType.ROW, StylingType.STYLE)

    def add_rows_classes(self, loc_indexer: Union[Any, Sequence[Any]], css_classes: Union[str, Sequence[str]]):
        self.model.modify_data(loc_indexer, css_classes, DataType.ROW, StylingType.CLASS)

    def remove_rows_styles(self, loc_indexer: Union[Any, Sequence[Any]],
                           css_styles: Union[Dict[str, str], Sequence[str]]):
        self.model.modify_data(loc_indexer, css_styles, DataType.ROW, StylingType.STYLE, False)

    def remove_rows_classes(self, loc_indexer: Union[Any, Sequence[Any]], css_classes: Union[str, Sequence[str]]):
        self.model.modify_data(loc_indexer, css_classes, DataType.ROW, StylingType.CLASS, False)

    def add_cells_styles(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                         css_styles: Dict[str, str]):
        self.model.modify_data((columns, rows), css_styles, DataType.CELL, StylingType.STYLE)

    def add_cells_classes(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                          css_classes: Union[str, Sequence[str]]):
        self.model.modify_data((columns, rows), css_classes, DataType.CELL, StylingType.CLASS)

    def remove_cells_styles(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                            css_styles: Union[Dict[str, str], Sequence[str]]):
        self.model.modify_data((columns, rows), css_styles, DataType.CELL, StylingType.STYLE, False)

    def remove_cells_classes(self, columns: Union[str, Sequence[str]], rows: Union[Any, Sequence[Any]],
                             css_classes: Union[str, Sequence[str]]):
        self.model.modify_data((columns, rows), css_classes, DataType.CELL, StylingType.CLASS, False)

    def add_index_style(self, styles: Union[Dict[str, str], Sequence[str]], level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, styles, DataType.INDEX, StylingType.STYLE)

    def add_index_class(self, css_classes: str, level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, css_classes, DataType.INDEX, StylingType.CLASS)

    def remove_index_style(self, styles: Union[Dict[str, str], Sequence[str]], level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, styles, DataType.INDEX, StylingType.STYLE, False)

    def remove_index_class(self, css_classes: str, level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, css_classes, DataType.INDEX, StylingType.CLASS, False)

    def add_header_style(self, styles: Union[Dict[str, str], Sequence[str]], level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, styles, DataType.HEADER, StylingType.STYLE)

    def add_header_class(self, css_classes: str, level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, css_classes, DataType.HEADER, StylingType.CLASS)

    def remove_header_style(self, styles: Union[Dict[str, str], Sequence[str]],
                            level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, styles, DataType.HEADER, StylingType.STYLE, False)

    def remove_header_class(self, css_classes: str, level: Union[int, Sequence[int]] = None):
        self.model.modify_data(level, css_classes, DataType.HEADER, StylingType.CLASS, False)


class ModelController:
    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False):

        self.logger = qf_logger.getChild(self.__class__.__name__)
        # Data Frame containing the table data
        self.data = QFDataFrame(data, index, columns, dtype, copy)
        # Dictionary containing a mapping from column names onto ColumnStyles
        self._columns_styles = {
            column_name: ColumnStyle(column_name)
            for column_name in self.data.columns.tolist()
        }
        # Series containing the styles for each of the rows
        self._rows_styles = QFSeries(data=[
            RowStyle(loc) for loc in self.data.index
        ], index=self.data.index)
        # Data Frame containing styles for all cells in the table, based upon columns_styles and rows_styles
        self._styles = QFDataFrame(data={
            column_name: [
                CellStyle(row_style, column_style) for row_style in self.rows_styles
            ] for column_name, column_style in self.columns_styles.items()
        }, index=self.data.index, columns=self.data.columns)
        self.table_styles = Style()
        self.index_styling = [Style() for level in range(0, index.nlevels)]
        self.header_styles = [Style() for level in range(0, columns.nlevels)]

    def modify_data(self, location: Optional[Union[Any, Sequence[Any], Tuple[Any, Any]]] = None,
                    data_to_update: Union[str, Dict[str, str], Sequence[str]] = None,
                    data_type: DataType = DataType.TABLE,
                    styling_type: StylingType = StylingType.STYLE,
                    modify_data: bool = True):
        """
        Main method that modifies the css style and/or class of different elements in the ModelController
        Parameters
        ----------
        location: Optional[Union[Any, Sequence[Any], Tuple[Any, Any]]]
            Should be the following, regarding the type of data_type:
            - column: Union[str, Sequence[str]]
            - rows: Union[Any, Sequence[Any]]
            - cells: Tuple[column, rows]
            - table: None
            - index: Union[int, Sequence[int], None]
            - header: Union[int, Sequence[int], None]
            Default is None
        data_to_update: Union[str, Dict[str, str], Sequence[str]]
            The actual css information that will be inserted/deleted from the model.
            Default is None
        data_type: DataType
            The type of data that needs to be modified.
            Default is DataType.TABLE
        styling_type: StylingType
            The type of styling that needs to be modified.
            Default is StylingType.STYLE
        modify_data: bool
            The type of data modification:
            - if True, then it is adding to the current list of css
            - if False, then it is removing from the current list of css
        """
        if data_type == DataType.INDEX:
            if location is None:
                list_of_modified_elements = self.index_styling
            else:
                location, _ = convert_to_list(location, int)
                list_of_modified_elements = [self.index_styling[i] for i in location if
                                             0 <= i < len(self.index_styling)]
        elif data_type == DataType.ROW:
            list_of_modified_elements = self.rows_styles.loc[location].tolist()
        elif data_type == DataType.COLUMN:
            location = location if isinstance(location, list) else [location]
            list_of_modified_elements = [self.columns_styles[column_name] for column_name in location]
        elif data_type == DataType.CELL:
            location = tuple([item] if not isinstance(item, list) else item for item in location)
            list_of_modified_elements = [self.styles.loc[row, column_name] for column_name in location[0] for row in
                                         location[1]]
        elif data_type == DataType.TABLE:
            list_of_modified_elements = [self.table_styles]
        elif data_type == DataType.HEADER:
            if location is None:
                list_of_modified_elements = self.header_styles
            else:
                location, _ = convert_to_list(location, int)
                list_of_modified_elements = [self.header_styles[i] for i in location if
                                             0 <= i < len(self.header_styles)]
        else:
            list_of_modified_elements = []

        for modified_element in list_of_modified_elements:
            self._add_styles_classes(modified_element, data_to_update, styling_type, modify_data)

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
                return CellStyle(row_style, column_style)

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
                column_name: ColumnStyle(column_name) for column_name in self.data.columns.tolist()
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
                RowStyle(loc) for loc in new_indices
            ], index=new_indices)

            self._rows_styles = self._rows_styles.append(new_row_styles, ignore_index=False)

        return self._rows_styles

    def _add_styles_classes(self, element, data_to_update, styling_type: StylingType, modify_data: bool = True):
        if styling_type == StylingType.STYLE:
            if modify_data:
                element.add_styles(data_to_update)
            else:
                element.remove_styles(data_to_update)
        elif styling_type == StylingType.CLASS:
            data_to_update, _ = convert_to_list(data_to_update, str)
            if modify_data:
                element.add_css_class(data_to_update)
            else:
                element.remove_css_class(data_to_update)
