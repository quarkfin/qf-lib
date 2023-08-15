import unittest

import pandas as pd

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.df_table import DFTable


class TestElements(unittest.TestCase):
    def setUp(self):
        # Sample data
        data = {
            ('General', 'Name'): ['John', 'Alice', 'Bob'],
            ('General', 'Age'): [28, 24, 22],
            ('Contact', 'Email'): ['john@example.com', 'alice@example.com', 'bob@example.com'],
            ('Contact', 'Phone'): ['123-456-7890', '987-654-3210', '555-555-5555'],
            ('Address', 'City'): ['New York', 'San Francisco', 'Los Angeles'],
            ('Address', 'Zip Code'): [10001, 94101, 90001]
        }

        # Create a DataFrame with MultiIndex for both rows and columns
        data_nested = pd.DataFrame(data)
        data_nested.index = pd.MultiIndex.from_tuples([('Person', 0), ('Person', 1), ('Person', 2)],
                                                      names=['Category', 'ID'])

        # Create a DataFrame with a MultiIndex for columns
        data_nested_html = DFTable(data_nested, css_classes=["table", "wide-first-column"], index_name="Sth custom")
        data_nested_html.add_index_class("wider-second-column")
        data_nested_html.add_index_class("center-align")
        data_nested_html.add_index_style({"background-color": "rgb(225, 0, 225)"}, 1)
        data_nested_html.add_index_style({"background-color": "rgb(100, 100, 5)"}, 0)
        data_nested_html.add_index_style({"color": "rgb(100, 0, 0)"})
        data_nested_html.add_index_style({"color": "rgb(0, 1, 0)"}, 2)
        data_nested_html.remove_index_style({"color": "rgb(0, 1, 0)"})
        dark_red = "#8B0000"
        data_nested_html.add_rows_styles(data_nested_html.model.data.index.tolist()[::2],
                                         {"background-color": "rgb(225, 225, 225)"})
        data_nested_html.add_columns_styles(data_nested_html.columns[0], {"width": "30%", "text-align": "center"})
        data_nested_html.add_columns_styles(data_nested_html.columns[0], {"color": "red"})
        data_nested_html.add_cells_styles(data_nested_html.columns[1],
                                          ("Person", 1),
                                          {"background-color": "rgb(100, 100, 255)", "color": dark_red})
        data_nested_html.add_cells_styles([data_nested_html.columns[0], data_nested_html.columns[4]],
                                          [("Person", 0), ("Person", 1)],
                                          {"background-color": "rgb(100, 255, 255)", "color": dark_red})

        data_nested_html.add_header_style({"background-color": "rgb(100, 100, 255)"}, [1, 0])
        data_nested_html.remove_header_style({"background-color": "rgb(200, 255, 255)"}, 1)

        self.data_nested_html = data_nested_html

        # Create a DataFrame with MultiIndex for both rows and columns
        data_nested_2 = pd.DataFrame(data)
        data_nested_2.index = pd.MultiIndex.from_tuples([('Person', 0), ('Person', 1), ('Person', 2)],
                                                        names=['Category', 'ID'])

        # Create a DataFrame with a MultiIndex for columns
        data_nested_2_html = DFTable(data_nested_2, css_classes=["table", "wide-first-column"])
        dark_red = "#8B08B0"
        data_nested_2_html.add_cells_styles([data_nested_2_html.columns[1], data_nested_2_html.columns[3]],
                                            [("Person", 1), ("Person", 2)],
                                            {"background-color": "rgb(255, 100, 255)", "color": dark_red})
        data_nested_2_html.add_header_style({"background-color": "rgb(0, 255, 0)"})
        self.data_nested_2_html = data_nested_2_html

    def test_index(self):
        self.assertTrue(self.data_nested_html.model.index_styling is not None)
        self.assertEqual(self.data_nested_html.model.index_styling[0].css_class,
                         ['wider-second-column', 'center-align'])
        self.assertEqual(self.data_nested_html.model.index_styling[0].css_class,
                         self.data_nested_html.model.index_styling[1].css_class)

        self.assertEqual(self.data_nested_html.model.index_styling[0].style, {'background-color': 'rgb(100,100,5)'})
        self.assertEqual(self.data_nested_html.model.index_styling[1].style, {'background-color': 'rgb(225,0,225)'})

        self.assertTrue(self.data_nested_2_html.model.index_styling[0].style == {})
        self.assertTrue(self.data_nested_2_html.model.index_styling[1].style == {})

    def test_columns(self):
        self.assertTrue(self.data_nested_html.model.columns_styles is not None)
        self.assertEqual(self.data_nested_html.model.columns_styles[('General', 'Name')].style,
                         {'width': '30%', 'text-align': 'center', 'color': 'red'})

    def test_rows(self):
        self.assertTrue(isinstance(self.data_nested_html.model.rows_styles, QFSeries))
        self.assertEqual(self.data_nested_html.model.rows_styles.values[-1].style,
                         {'background-color': 'rgb(225,225,225)'})

    def test_individual_cells(self):
        self.assertTrue(isinstance(self.data_nested_html.model.styles, QFDataFrame))
        self.assertTrue(self.data_nested_html.model.styles[("General", "Age")].iloc[1] is not None)
        self.assertTrue(self.data_nested_html.model.styles[("General", "Age")].iloc[1] is not None)
        self.assertEqual(self.data_nested_html.model.styles[("General", "Age")].iloc[1].style,
                         {'background-color': 'rgb(100,100,255)', 'color': '#8B0000'})

    def test_header(self):
        self.assertTrue(isinstance(self.data_nested_html.model.header_styles, list))
        self.assertTrue(isinstance(self.data_nested_2_html.model.header_styles, list))

        self.assertEqual(self.data_nested_html.model.header_styles[0].style, {'background-color': 'rgb(100,100,255)'})
        self.assertEqual(self.data_nested_html.model.header_styles[1].style, {})

        self.assertEqual(self.data_nested_2_html.model.header_styles[0].style,
                         self.data_nested_2_html.model.header_styles[1].style)


if __name__ == '__main__':
    unittest.main()
