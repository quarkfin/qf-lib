from qf_lib.common.utils.document_exporting import templates
from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.element import Element


class NewPageElement(Element):
    """
    This element will bring you to a new page of the pdf report
    """
    def __init__(self):
        """
        Constructs a new page element.
        """
        super().__init__()

    def generate_html(self, document: Document) -> str:
        """
        Generates the HTML that represents the jump to the new page.
        """
        env = templates.environment
        # the html templates are located in /src/common/templates
        template = env.get_template("new_page.html")
        return template.render()
