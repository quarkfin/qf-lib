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

import pandas as pd

from qf_lib.analysis.tearsheets.pandas_compat import count_assets_by_name, max_abs_exposure_by_name


class _Ticker:
    def __init__(self, name):
        self.name = name


class TestPandasCompat(unittest.TestCase):
    def setUp(self):
        ticker_a_front = _Ticker("A")
        ticker_a_next = _Ticker("A")
        ticker_b = _Ticker("B")
        self.positions_history = pd.DataFrame({
            ticker_a_front: [1.0, None, -2.0],
            ticker_a_next: [None, None, 3.0],
            ticker_b: [4.0, -5.0, None],
        })

    def test_count_assets_by_name(self):
        result = count_assets_by_name(self.positions_history)
        expected = pd.Series([2, 1, 1])
        pd.testing.assert_series_equal(result.reset_index(drop=True), expected, check_names=False)

    def test_max_abs_exposure_by_name(self):
        result = max_abs_exposure_by_name(self.positions_history)
        expected = pd.DataFrame({
            "A": [1.0, None, 3.0],
            "B": [4.0, 5.0, None],
        })
        pd.testing.assert_frame_equal(result.reset_index(drop=True), expected, check_names=False)


if __name__ == "__main__":
    unittest.main()
