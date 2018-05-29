from jinja2 import Template

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.element import Element


class ParagraphElement(Element):
    def __init__(self, text: str, grid_proportion=GridProportion.Eight):
        """
        Constructs a new Paragraph element.

        Parameters
        ----------
        text - The text to show in the paragraph.
        """
        super().__init__(grid_proportion)
        self._text = text

    def generate_html(self, document: Document) -> str:
        """
        Generates the underlying paragraph element's HTML.
        """
        text = self._text.replace('\n', '<br />')
        template = Template("<p>{{ text }}</p>")
        return template.render(text=text)
