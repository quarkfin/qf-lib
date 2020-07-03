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

import datetime
from typing import Any

from jinja2 import Template
from numpy import ScalarType

from qf_lib.common.utils.miscellaneous.constants import HIGHCHART_COLORS, HIGHCHART_DASH_STYLES
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class HorizontalLineDecorator(ChartDecorator, SimpleLegendItem):
    """
    A simple decorator that displays a horizontal line.

    Constructs a new horizontal line decorator. The ``plot_settings`` are passed directly to matplotlib's
    ``axhline``. See http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.axhline for valid settings.

    When plotting for the web, the ``plot_settings`` are passed directly to HighChart's plotLines options.
    """

    def __init__(self, y: ScalarType, color: str = 'k', key: str = None, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self._y = y
        self._color = color
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        # Save the line ID so that the legend can make use of it.
        self.legend_artist = chart.axes.axhline(y=self._y, color=self._color, **self.plot_settings)

    def decorate_html(self, chart: "Chart", chart_id: str) -> str:
        template = Template("""
            if (decorator_options.yAxis.plotLines === undefined) {
                decorator_options.yAxis.plotLines = [];
            }

            decorator_options.yAxis.plotLines.push({
                color: "{{ color }}",
                dashStyle: "{{ dash_style }}",
                value: {{ value }},
                width: 2,
                {% for key, value in plot_settings.items(): %}
                    {% if key in ["label"]: %}
                        {{ key }}: {{ value }},
                    {% endif %}
                {% endfor %}
            });
        """)

        color = HIGHCHART_COLORS.get(self._color, self._color)

        dash_style = HIGHCHART_DASH_STYLES.get(self.plot_settings["linestyle"], "")
        return template.render(value=self._y, color=color, dash_style=dash_style, decorator_id=self.key)


class VerticalLineDecorator(ChartDecorator, SimpleLegendItem):
    """
    A simple decorator that displays a vertical line.

    Constructs a new vertical line decorator. The ``plot_settings`` are passed directly to matplotlib's ``axvline``.
    See http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.axvline for valid settings.

    When plotting for the web, the ``plot_settings`` are passed directly to HighChart's plotLines options.

    """
    def __init__(self, x: ScalarType, color: str = 'k', key: str = None, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self._x = x
        self._color = color
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        # Save the line ID so that the legend can make use of it.
        self.legend_artist = chart.axes.axvline(x=self._x, color=self._color, **self.plot_settings)

    def decorate_html(self, chart: "Chart", chart_id: str) -> str:
        template = Template("""
            if (decorator_options.xAxis.plotLines === undefined) {
                decorator_options.xAxis.plotLines = [];
            }

            decorator_options.xAxis.plotLines.push({
                color: "{{ color }}",
                dashStyle: "{{ dash_style }}",
                value: moment({{ value }} * 1000).toDate(),
                width: 2,
                {% for key, value in plot_settings.items(): %}
                    {% if key in ["label"]: %}
                        {{ key }}: {{ value }},
                    {% endif %}
                {% endfor %}
            });
        """)
        # This assumes that the line chart's x-axis contains dates.
        assert isinstance(self._x, datetime.datetime)

        color = HIGHCHART_COLORS.get(self._color, self._color)

        dash_style = HIGHCHART_DASH_STYLES.get(self.plot_settings["linestyle"], "")
        return template.render(value=self._x.timestamp(), color=color, dash_style=dash_style,
                               plot_settings=self.plot_settings)


class DiagonalLineDecorator(ChartDecorator, SimpleLegendItem):
    """
    A simple decorator that displays a diagonal line.
    """

    def __init__(self, key: str = None, **plot_settings: Any):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        # Save the line ID so that the legend can make use of it.
        self.legend_artist = chart.axes.plot([0, 1], [0, 1], transform=chart.axes.transAxes, **self.plot_settings)
