import os
from os.path import join
from typing import Sequence

from qf_lib.common.utils.document_exporting import Document
from qf_lib.common.utils.document_exporting.element.header import HeaderElement
from qf_lib.common.utils.document_exporting.element.index import IndexElement
from qf_lib.settings import Settings
from qf_lib.starting_dir import get_starting_dir_abs_path


class DocumentExporter(object):
    """
    Abstract class for document_exporting of documents.
    """

    def __init__(self, settings: Settings):
        self._output_root_dir = join(get_starting_dir_abs_path(), settings.output_directory)

    def get_output_dir(self, export_dir: str) -> str:
        """
        Converts a partial path (`export_dir`) which is relative to the output root directory into a path which
        is relative to the current working directory.

        Parameters
        ----------
        export_dir
            relative path (relative to the output root directory) of the directory in which the generated document
            should be saved

        Returns
        -------
        absolute path of the directory in which the generated document should be saved
        """
        output_dir = os.path.join(self._output_root_dir, export_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        return output_dir

    @staticmethod
    def _merge_documents(documents: Sequence[Document], filename: str) -> Document:
        """
        Merges documents into a single document. All elements inside the documents are placed in the returned document.

        Parameters
        ----------
        documents
            a list of documents to merge
        filename
            The filename that should be applied to the resulting document.
        """
        result = Document(filename)
        for document in documents:
            for element in document.elements:
                result.add_element(element)

        return result

    @classmethod
    def _add_table_of_contents(cls, document):
        # Ideally we would like to add a table of contents after the Header element.
        # Check if a header element is the first element.
        if isinstance(document.elements[0], HeaderElement):
            # If it is the first element then insert the table of contents after it.
            document.elements.insert(1, IndexElement(4))
        else:
            # Otherwise insert it as the first element.
            document.elements.insert(0, IndexElement(4))
