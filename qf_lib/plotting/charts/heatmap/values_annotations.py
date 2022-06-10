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

import numpy as np
import seaborn.utils as sb_utils

from qf_lib.plotting.charts.heatmap.heatmap_chart_decorator import HeatMapChartDecorator


class ValuesAnnotations(HeatMapChartDecorator):
    """ Adds annotations containing values for each square presented on the heat map.

    Parameters
    ----------
    format_str: str
        The format of the annotation showed inside of each element of the heat map
    key
        see: Chart.__init__#key
    plot_settings
        additional keyword arguments passed to the matplotlib's Axes.text() method
    """

    def __init__(self, format_str='.2f', key=None, **plot_settings):
        super().__init__(key)
        self._plot_settings = plot_settings
        self._format_str = format_str

    def decorate(self, chart: "HeatMapChart"):
        mesh = chart.color_mesh_
        ax = chart.axes

        x_locs, y_locs = np.meshgrid(ax.get_xticks(), ax.get_yticks())
        values = mesh.get_array()
        mesh_facecolors = mesh.get_facecolors()

        for x, y, value, mesh_face_color in zip(x_locs.flat, y_locs.flat, values, mesh_facecolors):
            annotation = ("{:" + self._format_str + "}").format(value)

            text_color = self.get_text_color(mesh_face_color)
            plot_settings = dict(color=text_color, ha="center", va="center")
            plot_settings.update(self._plot_settings)
            ax.text(x, y, annotation, **plot_settings)

    def get_text_color(self, background_color):
        luminance = sb_utils.relative_luminance(background_color)
        text_color = ".15" if luminance > .408 else "w"
        return text_color
