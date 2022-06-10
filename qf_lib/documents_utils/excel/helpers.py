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

from openpyxl.utils import column_index_from_string
from openpyxl.utils.cell import coordinate_from_string


class BoundingBox:
    def __init__(self, starting_row: int, starting_column: int, ending_row: int, ending_column: int):
        self.starting_row = starting_row
        self.starting_column = starting_column
        self.ending_row = ending_row
        self.ending_column = ending_column


def row_and_column(cells_address: str) -> (int, int):
    """
    Converts the string address of the cell (e.g. A1) into the row's number (starting from 1) and column's number
    (starting from 1).
    """

    column_as_letter, row_number = coordinate_from_string(cells_address)
    column_number = column_index_from_string(column_as_letter)

    return row_number, column_number


def get_bounding_box(top_left_corner_cell: str, bottom_right_corner: str) -> BoundingBox:
    starting_row, starting_column = row_and_column(top_left_corner_cell)
    ending_row, ending_column = row_and_column(bottom_right_corner)

    return BoundingBox(starting_row, starting_column, ending_row, ending_column)
