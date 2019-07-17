from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class NewPageElement(Element):
    def __init__(self):
        """
        Relocates to a new page of the PDF report.
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
