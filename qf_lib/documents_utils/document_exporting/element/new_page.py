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

from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class NewPageElement(Element):
    def __init__(self):
        """
        Relocates to a new page of the PDF report.
        """
        super().__init__()

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the HTML that represents the jump to the new page.
        """
        env = templates.environment
        # the html templates are located in qf_lib/documents_utils/document_exporting/templates
        template = env.get_template("new_page.html")
        return template.render()
