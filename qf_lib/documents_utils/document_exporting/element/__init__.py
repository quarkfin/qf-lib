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
from typing import Optional

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting.document import Document


class Element:
    """Abstract class that defines a PDF Builder element, an single entity in a PDF such as a Chart or Paragraph."""

    def __init__(self, grid_proportion=GridProportion.Eight):
        self.grid_proportion = grid_proportion

    def generate_html(self, document: Optional[Document] = None) -> str:
        raise NotImplementedError()

    def get_grid_proportion_css_class(self) -> str:
        return str(self.grid_proportion)

    def get_grid_proportion(self) -> int:
        return self.grid_proportion.to_int()
