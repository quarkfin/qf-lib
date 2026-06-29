import unittest
from unittest.mock import patch

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from qf_lib.plotting.charts.boxplot_chart import BoxplotChart

matplotlib.use("Agg")


class TestBoxplotChart(unittest.TestCase):
    @patch("qf_lib.plotting.charts.boxplot_chart.sns.boxplot")
    def test_plot_does_not_pass_palette_without_hue(self, boxplot_mock):
        chart = BoxplotChart([pd.Series([1.0, 2.0]), pd.Series([3.0, 4.0])], linewidth=1)

        chart.plot()

        _, kwargs = boxplot_mock.call_args
        self.assertNotIn("palette", kwargs)
        self.assertIsInstance(kwargs["data"], pd.DataFrame)
        self.assertEqual(1, kwargs["linewidth"])
        plt.close(chart.figure)

    @patch("qf_lib.plotting.charts.boxplot_chart.sns.boxplot")
    def test_plot_keeps_palette_when_hue_is_provided(self, boxplot_mock):
        chart = BoxplotChart(
            pd.DataFrame({"value": [1.0, 2.0], "group": ["a", "b"]}),
            linewidth=1,
            hue="group",
        )

        chart.plot()

        _, kwargs = boxplot_mock.call_args
        self.assertIn("palette", kwargs)
        self.assertEqual("group", kwargs["hue"])
        plt.close(chart.figure)

    def test_plot_accepts_list_of_series_with_real_seaborn(self):
        chart = BoxplotChart([pd.Series([1.0, 2.0]), pd.Series([3.0, 4.0])], linewidth=1)

        chart.plot()

        self.assertIsNotNone(chart.axes)
        plt.close(chart.figure)


if __name__ == "__main__":
    unittest.main()
