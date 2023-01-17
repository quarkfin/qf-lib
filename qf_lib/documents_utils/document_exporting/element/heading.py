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

import uuid
from typing import Optional

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class HeadingElement(Element):
    def __init__(self, level: int, text: str, grid_proportion: GridProportion = GridProportion.Eight):
        """
        Represents an ordinary heading, usually used to start a new section in a document.

        Parameters
        ----------
        level
            The level of this heading, must be in range 1..6.
        text
            The text to display in the heading.
        """
        super().__init__(grid_proportion)
        self.level = level
        self.text = text
        self.id = "heading_" + str(uuid.uuid4())

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the HTML that represents the underlying heading.
        """
        env = templates.environment

        template = env.get_template("heading.html")
        return template.render(level=self.level, text=self.text, id=self.id)
