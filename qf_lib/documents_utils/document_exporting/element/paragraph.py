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
from typing import Union, Sequence, Optional

from jinja2 import Template

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class ParagraphElement(Element):
    def __init__(self, text: str, grid_proportion: GridProportion = GridProportion.Eight, css_classes:
                 Union[str, Sequence[str]] = ""):
        """
        Constructs a new Paragraph element.

        Parameters
        ----------
        text
            The text to show in the paragraph.
        """
        super().__init__(grid_proportion)
        self._text = text
        self._css_classes = ""
        self.set_css_classes(css_classes)

    def set_css_classes(self, css_classes: Union[str, Sequence[str]] = ""):
        css_classes, _ = convert_to_list(css_classes, str)

        def merge_classes(css_classes_list: Sequence[str]) -> str:
            return " ".join(css_classes_list)

        css_classes = merge_classes(css_classes)
        self._css_classes = css_classes

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the underlying paragraph element's HTML.
        """
        text = self._text.replace('\n', '<br />')
        css_classes = self._css_classes
        template = Template('<p class="{{ css_classes }}">{{ text }}</p>')
        return template.render(css_classes=css_classes, text=text)
