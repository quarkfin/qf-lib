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

from qf_lib.documents_utils.document_exporting import templates


class Document:
    """
    Represents a single PDF document. It is paired with the PDF builder which uses it to determine the PDF to
    create.
    """

    def __init__(self, name: str):
        self.elements = []
        self.parent_builder = None
        self.name = name
        self._generated_html = None  # Caching for generate_html.

    def generate_html(self) -> str:
        """
        Generates the HTML based on the elements in this document and returns it as a string.
        """
        if self._generated_html is not None:
            return self._generated_html

        env = templates.environment

        template = env.get_template("document.html")
        self._generated_html = template.render(elements=self.elements, document=self)
        return self._generated_html

    def add_element(self, element) -> None:
        """
        Appends a PDF element to this document's element list.
        """
        self.elements.append(element)
