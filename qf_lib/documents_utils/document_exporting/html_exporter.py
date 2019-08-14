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

import os.path
from typing import List

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.document_exporter import DocumentExporter
from qf_lib.settings import Settings


class HTMLExporter(DocumentExporter):
    """
    Stores a number of documents, which represent a single subreport, in order to then generate HTML for each of them.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def generate(self, documents: List[Document], export_dir: str, filename: str = None,
                 include_table_of_contents=True) -> List[str]:
        """
        Generates HTML pages for each document in this builder. The resulting HTML will be saved in
        the output directory, the filename will be the same as the Document's ``name`` field unless the
        ``filename`` parameter is specified, in which case there will only be one HTML file saved.
        """
        result = []

        self.logger.info("Generating HTML for website...")
        if filename is not None:
            documents = [self._merge_documents(documents, filename)]

        for document in documents:
            self.logger.info("Generating: {}".format(document.name))
            if include_table_of_contents:
                self._add_table_of_contents(document)

            # Generate the full document HTML.
            html = document.generate_html()

            # Find the output directory.
            output_dir = self.get_output_dir(export_dir)

            # Write out the HTML.
            assert len(document.name) > 0
            output_filename = os.path.join(output_dir, document.name) + ".html"

            with open(output_filename, "w") as file:
                file.write(html)

            result.append(output_filename)

        return result
