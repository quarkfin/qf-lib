from typing import Sequence, Union

from qf_lib.common.enums.axis import Axis
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxisTickLabelsDecorator(ChartDecorator):
    """
    Customizes tick labels for a given axis.
    """

    def __init__(self, axis: Axis, labels: Sequence[str] = None, tick_values: Sequence[float] = None,
                 rotation: Union[int, str] = None, key: str = None):
        """
        Parameters
        ----------
        axis
            X or Y Axis object
        labels
            a list of labels for ticks present in the Chart
        tick_values
            sequence of floats that will be used as ticks
        rotation
            rotation of selected axis labels. For example 20 = 20 degrees rotation
        key
            see: ChartDecorator.__init__#key
        """
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

        if self._labels is not None:
            axis.set_ticklabels(self._labels)

        if self._tick_values is not None:
            axis.set_ticks(self._tick_values)

        if self._rotation is not None:
            axis.set_tick_params(rotation=self._rotation)
