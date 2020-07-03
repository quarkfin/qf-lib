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

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesPositionDecorator(ChartDecorator):
    """
    Sets the position of the axes (the area of the chart) on the figure.

    Parameters
    ----------
    left: float
        expressed as values from 0 to 1
        left, bottom is the bottom left point of the Axis (excluding the ticks and ticks' labels)
    bottom: float
        expressed as values from 0 to 1
    width: float
        expressed as values from 0 to 1
    height: float
        expressed as values from 0 to 1
    key
        see ChartDecorator.key.__init__#key
    """

    def __init__(self, left: float, bottom: float, width: float, height: float, key: str = None):
        super().__init__(key)
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height

    def decorate(self, chart: "Chart") -> None:
        axes = chart.axes
        position = (self.left, self.bottom, self.width, self.height)
        axes.set_position(position)
