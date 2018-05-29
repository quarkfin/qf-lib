from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesPositionDecorator(ChartDecorator):
    """
    Sets the position of the axes (the area of the chart) on the figure.
    """

    def __init__(self, position, key: str=None):
        """
        Parameters
        ----------
        position
            [left, bottom, width, height] expressed as values form 0 to 1
            left bottom is the bottom left point of the Axis (excluding the ticks and ticks labels)
        key
            see ChartDecorator.key.__init__#key
        """
        super().__init__(key)
        self.position = position

    def decorate(self, chart) -> None:
        axes = chart.axes
        axes.set_position(self.position)
