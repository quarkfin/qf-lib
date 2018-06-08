import os
from typing import List

from os.path import join
from weasyprint import HTML, CSS

from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.document_exporter import DocumentExporter
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.get_sources_root import get_src_root
from qf_lib.settings import Settings


class PDFExporter(DocumentExporter):
    """
    Stores elements such as the ParagraphElement and ChartElement in order to build a PDF based on them once they
    have all been added.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._document_css_dir = join(get_src_root(), settings.document_css_directory)

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def generate(self, documents: List[Document], export_dir: str, filename: str,
                 include_table_of_contents=False, css_file_names: List[str] = None) -> List[str]:
        """
        Merged all documents into one and then exports the merged document to a PDF file in the given directory.

        Allows defining of multiple css files. The base css file will be applied first, followed sequentially
        by files defined in css_file_names.

        The CSS files must be placed in the Settings.document_css_directory directory.
        CSS files placed in Settings.document_css_directory/base will be applied for all exported PDF documents.

        Parameters
        ----------
        documents
            list of documents for which files should be generated
        export_dir
            relative path to the directory (relative to the output root directory) in which the PDF should be saved
        filename
            filename under which the merged document should be saved
        include_table_of_contents
            if True then table of contents will be generated at the beginning of the file
        css_file_names
            names of css files which should be applied for generating the PDF

        Returns
        -------
        the absolute path to the output PDF file that was saved
        """
        css_file_paths = []
        result = []
        documents = [self._merge_documents(documents, filename)]

        for document in documents:
            if include_table_of_contents:
                self._add_table_of_contents(document)

            # Generate the full document HTML
            self.logger.info("Generating HTML for PDF...")
            html = document.generate_html()

            # Find the output directory
            output_dir = self.get_output_dir(export_dir)

            # Automatically include all the css files in the `document_css/base` directory
            base_css = os.listdir(os.path.join(self._document_css_dir, "base"))
            for name in base_css:
                path = os.path.join(self._document_css_dir, "base", name)
                if os.path.isfile(path):
                    css_file_paths.append(CSS(path))

            # If we've set custom css files, add them to the pdf
            if css_file_names is not None:
                for name in css_file_names:
                    css_file_paths.append(CSS(os.path.join(self._document_css_dir, name + ".css")))

            # Parse the HTML.
            html = HTML(string=html)

            # Write out the PDF.
            output_filename = os.path.join(output_dir, filename)
            self.logger.info("Rendering PDF in {}...".format(output_filename))
            html.write_pdf(output_filename, css_file_paths)
            result.append(output_filename)

        return result
