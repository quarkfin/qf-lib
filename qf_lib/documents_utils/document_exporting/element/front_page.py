#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
from typing import Optional

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class FrontPage(Element):
    def __init__(self, header: str, title: str, subtitle: str, logo: str,
                 grid_proportion: GridProportion = GridProportion.Eight):
        """
        A stylised header element, consists of a major title (on left and right), subtitle and CERN logo.

        Parameters
        ----------
        header
            The header title.
        title
            The title below header, smaller typing.
        subtitle
            A title to show below the logo image.
        logo
            A filepath to the logo to display below the header, and centred on the page.
        """
        super().__init__(grid_proportion)
        self.header = header
        self.title = title
        self.subtitle = subtitle
        self.logo = logo

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the HTML that represents the underlying header.
        """
        env = templates.environment

        template = env.get_template("frontpage.html")
        return template.render(
            header=self.header, title=self.title, subtitle=self.subtitle, logo_url=self.logo)
