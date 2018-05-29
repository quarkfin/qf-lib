from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.document_exporting import templates
from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.element import Element


class HeaderElement(Element):
    """
    A stylised header element, consists of a major title (on left and right), subtitle and CERN logo.
    """
    def __init__(self, title: str, subtitle: str, title_right: str, logo: str, grid_proportion=GridProportion.Eight):
        """
        Constructs a new Header element.

        Parameters
        ----------
        title - The header title.
        subtitle - The header subtitle.
        title_right - A title to show on the right of the header.
        logo - A filepath to the logo to display on the left of the header.
        """
        super().__init__(grid_proportion)
        self.title = title
        self.subtitle = subtitle
        self.title_right = title_right
        self.logo = logo

    def generate_html(self, document: Document) -> str:
        """
        Generates the HTML that represents the underlying header.
        """
        env = templates.environment

        template = env.get_template("header.html")
        return template.render(title=self.title, subtitle=self.subtitle, title_right=self.title_right,
                               logo_url=self.logo)
