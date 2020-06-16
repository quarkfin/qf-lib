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

import os
from os.path import join, abspath, dirname
from typing import List

from weasyprint import HTML, CSS

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.document_exporter import DocumentExporter
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class PDFExporter(DocumentExporter):
    """
    Stores elements such as the ParagraphElement and ChartElement in order to build a PDF based on them once they
    have all been added. If there is a "document_css_directory" attribute set in the Settings, then CSS files from that
    directory will be applied for styling the output page. Otherwise the default styling will be applied.
    """

    DEFAULT_CSS_DIR_NAME = 'default_css'

    def __init__(self, settings: Settings):
        super().__init__(settings)

        if hasattr(settings, 'document_css_directory'):
            self._document_css_dir = join(get_starting_dir_abs_path(), settings.document_css_directory)
        else:
            this_dir_abs_path = abspath(dirname(__file__))
            self._document_css_dir = join(this_dir_abs_path, self.DEFAULT_CSS_DIR_NAME)

        self.logger = qf_logger.getChild(self.__class__.__name__)

    def set_default_directory_level_up(self):
        """
        Sets the document_css_dir one level above 'default css', to enable applying css classes in other folders.
        Using the generate function demands inputting css_file_names as paths from newly set level.
        e.g: 'default_css\main"
        """
        self._document_css_dir = abspath(dirname(__file__))

    def generate(self, documents: List[Document], export_dir: str, filename: str,
                 include_table_of_contents=False, css_file_names: List[str] = None) -> str:
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
        documents = [self._merge_documents(documents, filename)]

        # Find the output directory
        output_dir = self.get_output_dir(export_dir)
        output_filename = os.path.join(output_dir, filename)

        for document in documents:
            if include_table_of_contents:
                self._add_table_of_contents(document)

            # Generate the full document HTML
            self.logger.info("Generating HTML for PDF...")
            html = document.generate_html()

            # Automatically include all the css files in the `document_css/base` directory
            base_css = os.listdir(self._document_css_dir)
            for name in base_css:
                path = os.path.join(self._document_css_dir, name)
                if os.path.isfile(path):
                    css_file_paths.append(CSS(path))

            # If we've set custom css files, add them to the pdf
            if css_file_names is not None:
                for name in css_file_names:
                    css_file_paths.append(CSS(os.path.join(self._document_css_dir, name + ".css")))

            # Parse the HTML.
            html = HTML(string=html)

            # Write out the PDF.
            self.logger.info("Rendering PDF in {}...".format(output_filename))
            html.write_pdf(output_filename, css_file_paths)

        return output_filename
