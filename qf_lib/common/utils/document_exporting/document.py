from qf_lib.common.utils.document_exporting import templates


class Document(object):
    """
    Represents a single PDF document. It is paired with the PDF builder which uses it to determine the PDF to
    create.
    """
    def __init__(self, name: str):
        self.elements = []
        self.parent_builder = None
        self.name = name
        self._generated_html = None  # Caching for generate_html.

    def generate_html(self) -> str:
        """
        Generates the HTML based on the elements in this document and returns it as a string.
        """
        if self._generated_html is not None:
            return self._generated_html

        env = templates.environment

        template = env.get_template("document.html")
        self._generated_html = template.render(elements=self.elements, document=self)
        return self._generated_html

    def add_element(self, element) -> None:
        """
        Appends a PDF element to this document's element list.
        """
        self.elements.append(element)
