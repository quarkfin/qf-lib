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

import datetime
from typing import Optional

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element


class PageHeaderElement(Element):
    def __init__(self, logo_path: str = None, major_line: str = "", minor_line: str = "", date: datetime = None,
                 grid_proportion: GridProportion = GridProportion.Eight):
        """
        A stylised header element, consists of a major title (on left and right), subtitle and logo
        (loaded from the specified path).
        """
        super().__init__(grid_proportion)
        self.logo_path = logo_path

        self.major_line = major_line
        self.minor_line = minor_line

        if date is None:
            date = datetime.date.today()

        self.date = date_to_str(date, DateFormat.LONG_DATE)

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the HTML that represents the underlying header.
        """
        env = templates.environment

        template = env.get_template("page_header.html")
        return template.render(logo_path=self.logo_path,
                               major_line=self.major_line,
                               minor_line=self.minor_line,
                               date=self.date)
