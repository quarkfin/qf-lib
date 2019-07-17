from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class AxesPositionDecorator(ChartDecorator):
    """
    Sets the position of the axes (the area of the chart) on the figure.
    """

    def __init__(self, left: float, bottom: float, width: float, height: float, key: str = None):
        """
        Parameters
        ----------
        left, bottom, width, height
            expressed as values from 0 to 1
            left, bottom is the bottom left point of the Axis (excluding the ticks and ticks' labels)
        key
            see ChartDecorator.key.__init__#key
        """
        super().__init__(key)
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height

    def decorate(self, chart: "Chart") -> None:
        axes = chart.axes
        position = (self.left, self.bottom, self.width, self.height)
        axes.set_position(position)
