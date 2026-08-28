import unittest
from datetime import datetime

import pandas as pd

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.plotting.charts.boxplot_chart import BoxplotChart
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.helpers.create_return_quantiles import create_return_quantiles


class TestCreateReturnQuantiles(unittest.TestCase):
    def test_live_date_chart_keeps_six_box_layout_and_explicit_palette(self):
        returns = SimpleReturnsSeries(
            data=[0.01, 0.02, -0.01, 0.03],
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-08", "2020-02-05"]),
        )

        chart = create_return_quantiles(returns, live_start_date=datetime(2020, 1, 8))

        self.assertIsInstance(chart, BoxplotChart)
        self.assertIsInstance(chart._data, list)
        self.assertEqual(6, len(chart._data))
        self.assertTrue(all(isinstance(series, QFSeries) for series in chart._data))
        colors = Chart.get_axes_colors()
        expected_palette = [colors[i % len(colors)] for i in range(6)]
        self.assertEqual(expected_palette, chart.plot_settings["palette"])
        self.assertNotIn("hue", chart.plot_settings)

        try:
            chart.plot()
        finally:
            chart.close()

        self.assertIsNotNone(chart.axes)


if __name__ == "__main__":
    unittest.main()
