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

import matplotlib
import pandas as pd

from qf_lib.plotting.charts.boxplot_chart import BoxplotChart


matplotlib.use("Agg")


class TestBoxplotChart(unittest.TestCase):
    def test_plot_handles_list_of_series_without_hue(self):
        series_list = [
            pd.Series([1.0, 2.0, 3.0]),
            pd.Series([1.5, 2.5, 3.5]),
        ]
        chart = BoxplotChart(series_list, linewidth=1)

        try:
            chart.plot()
        finally:
            if chart.figure is not None:
                chart.close()

        self.assertIsNotNone(chart.axes)


if __name__ == "__main__":
    unittest.main()
