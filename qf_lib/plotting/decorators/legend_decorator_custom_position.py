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

import json
import textwrap
from jinja2 import Template
from qf_lib.common.enums.matplotlib_location import AxisLocation
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class LegendDecoratorCustomPosition(ChartDecorator):
    """
    A decorator which draws a legend on the graph. The legend titles are automatically determined based on what was
    specified during decorator creation and series addition.
    Uses custom forced legend position placement.

    Parameters
    -----------
     legend_placement: AxisLocation
        tuple(x-coordinate, y-coordinate), referencing placement of left bottom corner of legend box.
        Defines where the legend should be placed on the chart, in axis coordinates. e.g (1,0) bottom right corner
        of plot
    key: str
        the identifier of the decorator
    """

    def __init__(self, legend_placement: AxisLocation = AxisLocation.LOWER_RIGHT, key: str = None):
        super().__init__(key)
        self.legend_placement = legend_placement
        self.item_labels = []

    def add_entry(self, item: SimpleLegendItem, label: str) -> None:
        """
        Adds new entry to the legend.

        Parameters
        ----------
        item: SimpleLegendItem
            a decorator which should be described in the legend or the matplotlib's Artist object
        label: str
            a label which should be assigned to a given decorator
        """
        if not isinstance(label, str):
            label = str(label)
        self.item_labels.append((item, label))

    def decorate(self, chart: "Chart") -> None:
        axes = chart.axes
        if chart.secondary_axes is not None:
            axes = chart.secondary_axes

        # If there are no items to be included in the legend, don't show the legend at all
        if not self.item_labels:
            return

        handles = []
        labels = []
        for item, label in self.item_labels:
            handle = item.legend_artist
            assert handle is not None
            handles.append(handle)
            if label is None:
                label = '<no label>'
            adjusted_label = "\n".join(textwrap.wrap(label, width=60))
            labels.append(adjusted_label)

        axes.legend(handles, labels, loc=self.legend_placement.value)

    def decorate_html(self, chart: "Chart", chart_id: str) -> str:
        # For docs relating to this, see: http://api.highcharts.com/highcharts/legend
        template = Template("""
            window.chart_data["{{ chart_id }}"].legend_labels = {{ legend_labels }};
            decorator_options.legend = {
                enabled: true,
                labelFormatter: function () {
                    return window.chart_data["{{ chart_id }}"].legend_labels[this.name];
                }
            };""")

        legend_labels = {}
        for item, label in self.item_labels:
            legend_labels[item.key] = label
        return template.render(chart_id=chart_id, legend_labels=json.dumps(legend_labels))
