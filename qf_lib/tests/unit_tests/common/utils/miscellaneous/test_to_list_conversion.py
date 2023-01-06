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
from unittest import TestCase

from pandas import Index

from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.tests.unit_tests.backtesting.portfolio.dummy_ticker import DummyTicker


class TestToListConversion(TestCase):

    def test_convert_to_list_single_element(self):
        single_elements = [DummyTicker("Ticker Example"), 17, 17.5, "X", "long string", None, False]

        for element in single_elements:
            with self.subTest(f"Test convert_to_list with single element {element} of type {type(element)}",
                              element=element):
                list_of_elements, was_conversion_necessary = convert_to_list(element, type(element))
                self.assertTrue(was_conversion_necessary)
                self.assertCountEqual([element], list_of_elements)

    def test_convert_to_list_list_of_strings(self):
        list_of_strings = ["welcome", "to", "the", "jungle"]
        list_of_elements, was_conversion_necessary = convert_to_list(list_of_strings, str)
        self.assertFalse(was_conversion_necessary)
        self.assertEqual(list_of_strings, list_of_elements)

    def test_convert_to_list_type_mismatch(self):
        list_of_strings = ["welcome", "to", "the", "jungle"]
        with self.assertRaises(ValueError):
            convert_to_list(list_of_strings, int)

    def test_convert_to_list_list_of_integers(self):
        list_of_integers = [42, 13, 26]
        list_of_elements, was_conversion_necessary = convert_to_list(list_of_integers, int)
        self.assertFalse(was_conversion_necessary)
        self.assertEqual(list_of_integers, list_of_elements)

    def test_convert_to_list_list_with_various_types(self):
        list_with_various_types = [42, 13, "bonjour", "welcome"]
        list_of_elements, was_conversion_necessary = convert_to_list(list_with_various_types, (int, str))
        self.assertFalse(was_conversion_necessary)
        self.assertEqual(list_with_various_types, list_of_elements)

    def test_convert_to_list_list_of_floats(self):
        list_of_floats = [42.0, 13.5, 26.0]
        list_of_elements, was_conversion_necessary = convert_to_list(list_of_floats, float)
        self.assertFalse(was_conversion_necessary)
        self.assertEqual(list_of_floats, list_of_elements)

    def test_convert_to_list_pandas_index(self):
        index = Index(data=["hello", "bonjour"])
        with self.assertRaises(ValueError):
            convert_to_list(index, str)

    def test_convert_to_list_qfseries(self):
        series = QFSeries(data=["hello", "bonjour"])
        with self.assertRaises(ValueError):
            convert_to_list(series, str)
