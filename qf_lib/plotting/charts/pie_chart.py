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
from typing import Tuple, Optional

import numpy as np

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class PieChart(Chart):
    """
    Initialize the pie chart plotting class.

    Parameters
    ----------
    sort_values : bool
        If True (default), the data series will be sorted in ascending order before plotting.
    arrows : bool
        If True (default), use arrows to point from the pie chart to the labels outside the chart.
        If False, labels will be placed directly on the pie chart.
    autotext_colour : str or None
        Colour to apply to the automatic percentage labels displayed on the pie chart (only applies if `arrows=False`).
        If None, the default Matplotlib color is used.
    **plot_settings : Dict
        Additional keyword arguments for customizing the plot appearance, such as `explode`, `autopct`, `textprops`, etc.

    """

    def __init__(self, sort_values: Optional[bool] = True, arrows: Optional[bool] = True,
                 autotext_colour: Optional[str] = None, **plot_settings):
        super().__init__()
        self.plot_settings = plot_settings
        self.sort_values = sort_values
        self.arrows = arrows
        self._item_labels = []
        self._autotext_colour = autotext_colour

    def plot(self, figsize: Tuple[float, float] = None) -> None:
        self._setup_axes_if_necessary(figsize=figsize)
        self._apply_decorators()
        self._adjust_style()

    def _apply_decorators(self) -> None:
        from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
        from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator

        # First the Data Element Decorator needs to be applied before any other decorator can be added
        data_element_decorators = [d for d in self._decorators.values() if isinstance(d, DataElementDecorator)]
        self.apply_data_element_decorators(data_element_decorators)

        for decorator in self._decorators.values():
            if isinstance(decorator, LegendDecorator):
                decorator.item_labels = self._item_labels
            decorator.decorate(self)

    def add_decorator(self, decorator: ChartDecorator) -> None:
        """
        Adds the new decorator to the chart.

        Each decorator must have a unique key that also doesn't clash with any series keys because both are used
        for legend label data. If there is already a decorator registered under the specified key, the operation
        will raise the AssertionError.

        Note: In case of PieCharts it is ensured that there exists only a single DataElementDecorator and max
        one LegendDecorator.

        Parameters
        ------------
        decorator: ChartDecorator
            decorator to be added
        """
        key = decorator.key
        assert key not in self._decorators, "The key '{}' is already used for another decorator.".format(key)

        from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
        from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
        if isinstance(decorator, (LegendDecorator, DataElementDecorator)):
            for existing in self._decorators.values():
                if isinstance(existing, type(decorator)):
                    raise ValueError(f"Only one instance of {type(decorator).__name__} is allowed.")

        self._decorators[key] = decorator

    def apply_data_element_decorators(self, data_element_decorators):
        if len(data_element_decorators) > 1:
            raise ValueError("Only a single DataElementDecorator is supported by PieChart class.")
        data_element = data_element_decorators[0]

        series = data_element.data
        if not isinstance(series, QFSeries):
            raise ValueError(f"The passed DataElementDecorator is not a QFSeries: {series}.")

        series = series.sort_values() if self.sort_values else series

        plot_kwargs = self.plot_settings
        plot_kwargs.setdefault('autopct', '%1.1f%%' if not self.arrows else None)
        plot_kwargs.setdefault('explode', [0.01] * len(series))

        if not self.arrows:
            labels = [f"{index}" for index, value in series.items()]
            wedges, texts, autotexts = self.axes.pie(series, labels=labels, startangle=90, counterclock=False,
                                                     **plot_kwargs)
            item_labels = [(SimpleLegendItem(w), t.get_text()) for w, t in zip(wedges, texts)]

            # Adjust autotext colours
            if self._autotext_colour is not None:
                for autotext in autotexts:
                    autotext.set_color(self._autotext_colour)
        else:

            plot = self.axes.pie(series, labels=None, startangle=90, counterclock=False, **plot_kwargs)
            series_sum = series.sum()
            labels = [f"{index}, {value / series_sum:.1%}" for index, value in series.items()]
            item_labels = [(SimpleLegendItem(w), t) for w, t in zip(plot[0], series.keys())]

            kw = {
                'arrowprops': {
                    'arrowstyle': '-',
                    'color': 'black'
                },
                'zorder': 0,
                'va': 'center',
                **plot_kwargs.get('textprops', {})
            }

            for i, p in enumerate(plot[0]):
                angle = (p.theta2 - p.theta1) / 2. + p.theta1
                y = np.sin(np.deg2rad(angle))
                x = np.cos(np.deg2rad(angle))
                yc = np.arcsin(y) / (np.pi / 2)
                connection_style = f"angle,angleA=0,angleB={angle}"

                kw["arrowprops"].update({"connectionstyle": connection_style})
                horizontal_alignment = "right" if x <= 0 else "left"

                label_pos = ((1.1 + (i % 2) * 0.2) * np.sign(x), 1.2 * yc)

                self.axes.annotate(labels[i], xy=(0.9 * x, 0.9 * y), xytext=label_pos,
                                   horizontalalignment=horizontal_alignment, **kw)

        self._item_labels = item_labels
