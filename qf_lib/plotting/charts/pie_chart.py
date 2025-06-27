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
from itertools import cycle
from typing import Tuple, Optional

import numpy as np

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem

"""
Changes
- removes slices distance, now explode needs to be provided, default is stil 0.01
"""


class PieChart(Chart):
    """
    Pie chart util class, it can plot only QFSeries.

    Parameters
    ----------
    data: QFSeries
        The series to plot in the pie chart.
    sort_values:
    plot_settings
        Options to pass to the ``pie`` function.
    """
    def __init__(self, sort_values: Optional[bool] = True, arrows: Optional[bool] = True, **plot_settings):
        super().__init__()
        self.plot_settings = plot_settings
        self.sort_values = sort_values
        self.arrows = arrows
        self._item_labels = []

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize=figsize)

        self._apply_decorators()
        self._adjust_style()

    def _apply_decorators(self) -> None:
        from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
        from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator

        legend_decorators = []
        regular_decorators = []
        data_element_decorators = []

        for decorator in self._decorators.values():
            if isinstance(decorator, LegendDecorator):
                legend_decorators.append(decorator)
            elif isinstance(decorator, DataElementDecorator):
                data_element_decorators.append(decorator)
            else:
                regular_decorators.append(decorator)

        if data_element_decorators:
            self.apply_data_element_decorators(data_element_decorators)

        for decorator in regular_decorators:
            decorator.decorate(self)

        if legend_decorators:
            decorator = legend_decorators[0]
            decorator.item_labels = self._item_labels
            decorator.decorate(self)

    def apply_data_element_decorators(self, data_element_decorators):
        plot_kwargs = self.plot_settings

        for i, data_element in enumerate(data_element_decorators):
            series = data_element.data
            if not isinstance(series, QFSeries):
                raise ValueError(f"The passed DataElementDecorator is not a QFSeries: {series}.")

            colors = cycle(Chart.get_axes_colors())

            if 'explode' not in self.plot_settings:
                plot_kwargs['explode'] = [0.01 for _ in range(len(series))]

            plot_settings = data_element.plot_settings.copy()
            plot_settings.setdefault("color", next(colors))

            series = series.sort_values() if self.sort_values else series


            if not self.arrows:
                if 'autopct' not in plot_kwargs:
                    plot_kwargs['autopct'] = '%1.1f%%'

                labels = [f"{index}" for index, value in series.items()]
                plot = self.axes.pie(series, labels=labels, startangle=90, counterclock=False, **plot_kwargs)
                self._item_labels = [(SimpleLegendItem(w), t.get_text()) for w, t in zip(plot[0], plot[1])]

            else:

                plot = self.axes.pie(series, labels=None, startangle=90, counterclock=False, **plot_kwargs)
                series_sum = series.sum()
                labels = [f"{index}, {value / series_sum:.1%}" for index, value in series.items()]

                self._item_labels = [(SimpleLegendItem(w), t) for w, t in zip(plot[0], series.keys())]

                arrow_props = {
                    'arrowstyle': '-',
                    'color': 'black'
                }
                kw = {
                    'arrowprops': arrow_props,
                    'zorder': 0,
                    'va': 'center',
                    **plot_kwargs['textprops']
                }

                for i, p in enumerate(plot[0]):
                    angle = (p.theta2 - p.theta1) / 2. + p.theta1
                    y = np.sin(np.deg2rad(angle))
                    x = np.cos(np.deg2rad(angle))
                    yc = np.arcsin(y) / (np.pi / 2)
                    connection_style = f"angle,angleA=0,angleB={angle}"

                    kw["arrowprops"].update({"connectionstyle": connection_style})
                    horizontal_alignment = "right" if x <= 0 else "left"

                    label_pos = ((1.3 + (i % 2) * 0.4) * np.sign(x), 1.4 * yc)

                    self.axes.annotate(labels[i], xy=(0.8 * x, 0.8 * y), xytext=label_pos,
                                       horizontalalignment=horizontal_alignment, **kw)
