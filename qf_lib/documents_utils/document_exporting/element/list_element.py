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
from typing import List, Optional

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class ListElement(Element):
    def __init__(self, elements: List[Element], grid_proportion: GridProportion = GridProportion.Eight):
        """
        Represents a list of strings.

        Parameters
        ----------
        elements: List[Element]
            list of elements that should be outputted as an unordered list
        """
        super().__init__(grid_proportion)
        self.elements = elements

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the underlying HTML for this List element.
        """
        # Generate the HTML.
        env = templates.environment
        template = env.get_template("list.html")
        return template.render(elements=self.elements)
