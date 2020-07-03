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

from typing import TypeVar, Any

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator

XAxisCoordinate = TypeVar("XAxisCoordinate")


class VerticalSpanDecorator(ChartDecorator):
    """
    Draws a vertical span (rectangle) from x_min to x_max.

    Parameters
    ----------
    x_min: XAxisCoordinate
        x at which the vertical span should start (expressed in DATA coordinates)
    x_max: XAxisCoordinate
        x at which the vertical span should end (expressed in DATA coordinates)
    y_min: float
        y at which the vertical span should start (expressed in AXES coordinates)
    y_max: float
        y at which the vertical span should end (expressed in AXES coordinates)
    key: str
        see: ChartDecorator.__init__#key
    plot_settings
        additional arguments which will be passed to the matplotlib plotting function
    """

    def __init__(self, x_min: XAxisCoordinate, x_max: XAxisCoordinate, y_min: float = 0, y_max: float = 1,
                 key: str = None, **plot_settings: Any):
        super().__init__(key)
        self.x_min = x_min
        self.x_max = x_max

        assert 0.0 <= y_min <= 1.0
        assert 0.0 <= y_max <= 1.0
        self.y_min = y_min
        self.y_max = y_max

        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        plot_settings = self.plot_settings.copy()
        plot_settings.setdefault('facecolor', 'lightblue')
        plot_settings.setdefault('alpha', 0.5)

        chart.axes.axvspan(self.x_min, self.x_max, self.y_min, self.y_max, **plot_settings)
