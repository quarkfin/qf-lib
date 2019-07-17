import uuid

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class HeadingElement(Element):
    def __init__(self, level: int, text: str, grid_proportion: GridProportion = GridProportion.Eight):
        """
        Represents an ordinary heading, usually used to start a new section in a document.

        Parameters
        ----------
        level
            The level of this heading, must be in range 1..6.
        text
            The text to display in the heading.
        """
        super().__init__(grid_proportion)
        self.level = level
        self.text = text
        self.id = "heading_" + str(uuid.uuid4())

    def generate_html(self, document: Document) -> str:
        """
        Generates the HTML that represents the underlying heading.
        """
        env = templates.environment

        template = env.get_template("heading.html")
        return template.render(level=self.level, text=self.text, id=self.id)
