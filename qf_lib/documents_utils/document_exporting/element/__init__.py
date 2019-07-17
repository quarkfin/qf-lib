from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting.document import Document


class Element:
    """Abstract class that defines a PDF Builder element, an single entity in a PDF such as a Chart or Paragraph."""

    def __init__(self, grid_proportion=GridProportion.Eight):
        self.grid_proportion = grid_proportion

    def generate_html(self, document: Document) -> str:
        raise NotImplementedError()

    def get_grid_proportion_css_class(self) -> str:
        return str(self.grid_proportion)
