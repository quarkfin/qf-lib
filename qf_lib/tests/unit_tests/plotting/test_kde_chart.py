import unittest
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np

from qf_lib.plotting.charts.kde_chart import KDEChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


class TestKDEChart(unittest.TestCase):
    @patch("qf_lib.plotting.charts.kde_chart.sns.kdeplot")
    def test_apply_data_element_decorators_maps_deprecated_seaborn_kwargs(self, kdeplot_mock):
        chart = KDEChart()
        _, axes = plt.subplots()
        self.addCleanup(plt.close, chart.figure)
        chart.axes = axes
        decorator = DataElementDecorator(
            np.array([0.0, 1.0, 2.0]), bw="scott", shade=True, label="series", color="blue"
        )

        chart.apply_data_element_decorators([decorator])

        kdeplot_mock.assert_called_once()
        _, kwargs = kdeplot_mock.call_args
        self.assertEqual("scott", kwargs["bw_method"])
        self.assertTrue(kwargs["fill"])
        self.assertNotIn("bw", kwargs)
        self.assertNotIn("shade", kwargs)
        self.assertEqual("series", kwargs["label"])
        self.assertEqual("blue", kwargs["color"])


if __name__ == "__main__":
    unittest.main()
