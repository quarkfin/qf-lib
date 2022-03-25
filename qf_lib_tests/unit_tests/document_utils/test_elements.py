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

import unittest

from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element.header import HeaderElement


class TestElements(unittest.TestCase):
    def setUp(self):
        self.document = Document("")

    def test_header_generation(self):
        header = HeaderElement("CERN Pension Fund", "Macro Dashboard", "Quantitative Methods Section", "logo.png")
        html = header.generate_html(self.document)
        assert "CERN Pension Fund" in html


if __name__ == '__main__':
    unittest.main()
