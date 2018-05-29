from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.element import Element


class CustomElement(Element):
    """
    An element containing custom HTML.
    """
    def __init__(self, html: str, grid_proportion=GridProportion.Eight):
        """
        Constructs a new Custom element.
        """
        super().__init__(grid_proportion)
        self.html = html

    def generate_html(self, document: Document) -> str:
        """
        Generates the HTML that represents the underlying element.
        """
        return self.html
