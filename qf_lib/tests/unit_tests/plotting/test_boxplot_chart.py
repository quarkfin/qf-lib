import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.boxplot_chart import BoxplotChart


class TestBoxplotChart(unittest.TestCase):
    @patch("qf_lib.plotting.charts.boxplot_chart.sns.boxplot")
    def test_plot_passes_qf_dataframe_to_seaborn(self, boxplot_mock):
        palette = ["#112233", "#445566"]
        chart = BoxplotChart(
            [QFSeries([1.0, 2.0]), QFSeries([3.0, 4.0])],
            linewidth=1,
            palette=palette,
        )

        chart.plot()

        _, kwargs = boxplot_mock.call_args
        self.assertIsInstance(kwargs["data"], QFDataFrame)
        self.assertEqual(palette, kwargs["palette"])
        self.assertEqual(1, kwargs["linewidth"])
        plt.close(chart.figure)

    def test_plot_accepts_list_of_series_with_real_seaborn(self):
        chart = BoxplotChart(
            [QFSeries([1.0, 2.0]), QFSeries([3.0, 4.0])],
            linewidth=1,
            palette=["#112233", "#445566"],
        )

        try:
            chart.plot()
        finally:
            chart.close()

        self.assertIsNotNone(chart.axes)


if __name__ == "__main__":
    unittest.main()
