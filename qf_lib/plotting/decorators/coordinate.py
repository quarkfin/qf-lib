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

import matplotlib.transforms as mtransform


class Coordinate:
    """
    Base class for coordinates.
    """

    def __init__(self, value: object):
        self.value = value

    def get_transformation(self, chart: "Chart") -> mtransform.Transform:
        """
        Returns the proper transformation which transforms coordinate from the absolute system to a specific one
        (depends on the implementation).
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
