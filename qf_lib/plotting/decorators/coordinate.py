import matplotlib.transforms as mtransform


class Coordinate(object):
    """
    Base class for coordinates.
    """

    def __init__(self, value: object):
        self.value = value

    def get_transformation(self, chart: "Chart") -> mtransform.Transform:
        """
            Returns the proper transformation which transforms coordinate from the absolute system to a given one.
        """
        raise NotImplementedError()


class DataCoordinate(Coordinate):
    """ Coordinate which is bound to data (e.g. coordinate being a certain point on x-axis). """

    def get_transformation(self, chart: "Chart") -> mtransform.Transform:
        return chart.axes.transData


class AxesCoordinate(Coordinate):
    """
    Coordinate which is bound to Axes object (e.g. right side of the Axes).
    In this system point (0,0) is a bottom left of the axes.
    """

    def __init__(self, value: float):
        assert 0.0 <= value <= 1.0
        super().__init__(value)

    def get_transformation(self, chart: "Chart") -> mtransform.Transform:
        return chart.axes.transAxes


class FigureCoordinate(Coordinate):
    """
    Coordinate which is bound to Figure object (e.g. top of the Figure).
    In this system point (0,0) is a bottom left of the figure.
    """
    def __init__(self, value: float):
        assert 0.0 <= value <= 1.0
        super().__init__(value)

    def get_transformation(self, chart: "Chart") -> mtransform.Transform:
        return chart.figure.transFigure


class DisplayCoordinate(Coordinate):
    """
    Coordinate which is bound to Display (absolute values).
    In this system point (0,0) is a bottom left of the display.
    """

    def __init__(self, value: float):
        assert 0.0 <= value <= 1.0
        super().__init__(value)

    def get_transformation(self, chart: "Chart") -> mtransform.Transform:
        return mtransform.IdentityTransform()
