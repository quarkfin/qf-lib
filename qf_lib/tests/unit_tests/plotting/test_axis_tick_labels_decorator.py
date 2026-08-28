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
import warnings
from unittest import TestCase
from unittest.mock import Mock

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from qf_lib.common.enums.axis import Axis  # noqa: E402
from qf_lib.plotting.decorators.axis_tick_labels_decorator import (  # noqa: E402
    AxisTickLabelsDecorator,
)

LABELS = ["alpha", "beta", "gamma"]


class TestAxisTickLabelsDecorator(TestCase):
    def setUp(self):
        self.figure, self.axes = plt.subplots()
        # a plain plot keeps the default (non-fixed) locator, which is the
        # situation in which setting fixed labels warns
        self.axes.plot([0, 1, 2], [1, 2, 3])
        self.chart = Mock()
        self.chart.axes = self.axes

    def tearDown(self):
        plt.close(self.figure)

    def _decorate(self, **kwargs):
        decorator = AxisTickLabelsDecorator(axis=Axis.X, **kwargs)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            decorator.decorate(self.chart)
            self.figure.canvas.draw()
        return [w for w in caught if "FixedFormatter" in str(w.message)]

    def test_rotated_labels_do_not_warn(self):
        self.assertEqual(self._decorate(labels=LABELS, rotation=45), [])

    def test_rotated_labels_with_auto_rotation_do_not_warn(self):
        self.assertEqual(self._decorate(labels=LABELS, rotation="auto"), [])

    def test_labels_without_rotation_do_not_warn(self):
        self.assertEqual(self._decorate(labels=LABELS), [])

    def test_rotated_labels_with_explicit_tick_values_do_not_warn(self):
        self.assertEqual(
            self._decorate(labels=LABELS, rotation=45, tick_values=[0, 1, 2]), []
        )

    def test_rotated_labels_are_still_applied(self):
        self._decorate(labels=LABELS, rotation=45)

        rendered = [tick.get_text() for tick in self.axes.get_xticklabels()]
        self.assertEqual(rendered, LABELS)
        self.assertEqual(self.axes.get_xticklabels()[0].get_rotation(), 45.0)


if __name__ == "__main__":
    unittest.main()
