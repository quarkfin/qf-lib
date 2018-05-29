import logging
import os.path
from typing import List

from qf_lib.common.utils.document_exporting import Document
from qf_lib.common.utils.document_exporting.document_exporter import DocumentExporter
from qf_lib.settings import Settings


class HTMLExporter(DocumentExporter):
    """
    Stores a number of documents, which represent a single subreport, in order to then generate HTML for each of them.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.logger = logging.getLogger(self.__class__.__name__)

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
