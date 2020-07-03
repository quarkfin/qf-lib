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

from typing import Any

from matplotlib import transforms
from matplotlib.artist import Artist

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.coordinate import Coordinate


class TextDecorator(ChartDecorator):
    """
    Adds text to the Chart at given coordinates (e.g. the label for data point).

    Parameters
    ----------
    text: str
        Text which should be added to the chart
    x: Coordinate
        x coordinate for the text
    y: Coordinate
        y coordinate for the text
    key: str
        see: ChartDecorator.__init__#key
    plot_settings
        additional arguments which will be passed to the matplotlib plotting function
        (see: http://matplotlib.org/api/text_api.html#matplotlib.text.Text)
    """

    def __init__(self, text: str, x: Coordinate, y: Coordinate, key: str = None, **plot_settings: Any) -> None:
        super().__init__(key)
        self.text = text
        self.x = x
        self.y = y
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        x_transform = self.x.get_transformation(chart)
        y_transform = self.y.get_transformation(chart)

        transformation = transforms.blended_transform_factory(x_transform, y_transform)
        plot_settings = self.plot_settings.copy()

        plot_settings['transform'] = transformation

        # clipping of the text should be turned on, if not specified otherwise
        plot_settings.setdefault('clip_on', True)

        text_artist = chart.axes.text(x=self.x.value, y=self.y.value, s=self.text, **plot_settings)
        self._update_axes_datalim(chart, text_artist)

    def _update_axes_datalim(self, chart: "Chart", text_artist: Artist):
        """
        Extends the area of the Axes in a chart so that text is shown correctly (isn't clipped).
        """
        bbox = text_artist.get_window_extent(chart.figure.canvas.get_renderer())
        ax = chart.axes
        bbox_data = bbox.transformed(ax.transData.inverted())
        ax.update_datalim(bbox_data.corners())
        ax.autoscale_view()
