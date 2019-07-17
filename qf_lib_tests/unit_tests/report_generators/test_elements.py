import unittest

try:
    from qf_lib.documents_utils.document_exporting.element import HeaderElement
    from qf_lib.documents_utils.document_exporting.document import Document
except ImportError:
    raise unittest.SkipTest("Could not import PDF Builder. Assuming that weasyprint is missing.")


class TestElements(unittest.TestCase):
    def setUp(self):
        self.document = Document("")

    def test_header_generation(self):
        header = HeaderElement("CERN Pension Fund", "Macro Dashboard", "Quantitative Methods Section", "logo.png")
        html = header.generate_html(self.document)
        assert "CERN Pension Fund" in html


if __name__ == '__main__':
    unittest.main()
