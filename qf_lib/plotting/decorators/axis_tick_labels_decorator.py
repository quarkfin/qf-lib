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

from typing import Sequence, Union

from qf_lib.common.enums.axis import Axis
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxisTickLabelsDecorator(ChartDecorator):
    """
    Customizes tick labels for a given axis.

    Parameters
    ----------
    axis: Axis
        X or Y Axis object
    labels: Sequence[str]
        a list of labels for ticks present in the Chart
    tick_values: Sequence[float]
        sequence of floats that will be used as ticks
    rotation: int, str
        rotation of selected axis labels. For example 20 = 20 degrees rotation
    key: str
        see: ChartDecorator.__init__#key
    """

    def __init__(self, axis: Axis, labels: Sequence[str] = None, tick_values: Sequence[float] = None,
                 rotation: Union[int, str] = None, key: str = None):
        super().__init__(key)
        self._labels = labels
        self._axis = axis
        self._rotation = rotation
        self._tick_values = tick_values

    def decorate(self, chart: "Chart"):
        if self._axis == Axis.X:
            axis = chart.axes.xaxis
        elif self._axis == Axis.Y:
            axis = chart.axes.yaxis
        else:
            raise ValueError("Supported axis: Axis.X and Axis.Y")

        if self._tick_values is not None:
            axis.set_ticks(self._tick_values)

        if self._labels is not None:
            axis.set_ticklabels(self._labels)

        if self._rotation is not None:
            axis.set_tick_params(rotation=self._rotation)
