from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement


class IndexElement(Element):
    def __init__(self, max_level: int = 2, grid_proportion: GridProportion = GridProportion.Eight):
        """
        Represents a Table of Contents. It is automatically generated based on the headings in the parent document.

        Parameters
        ----------
        max_level
            the max heading level to show in the index.
        """
        super().__init__(grid_proportion)
        self.max_level = max_level

    def generate_html(self, document: Document) -> str:
        """
        Generates the underlying HTML for this Index element. The generated index is based on the headings in the
        document that this ``IndexElement`` was added to.
        """

        # Filter out any non-heading elements as the template is not interested in anything else.
        elems = []
        for element in document.elements:
            if isinstance(element, HeadingElement):
                if element.level <= self.max_level:
                    elems.append(element)

        # Generate the HTML.
        env = templates.environment

        template = env.get_template("index.html")
        return template.render(elements=elems)
