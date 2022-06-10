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

import threading
from collections import Sequence
from typing import Tuple

from mpl_toolkits.mplot3d import Axes3D  # important to keep this line for figure.add_subplot(1, 1, 1, projection='3d')

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


class SurfaceChart3D:
    """
     Creates a 3D surface chart

    Parameters
    ----------
    x_vector: Sequence
        vector corresponding to points on X axis
    y_vector: Sequence
        vector corresponding to points on Y axis
    z_matrix: numpy.array
        matrix with values. The shape of the Z matrix has to be [len(Y), len(X)]
        X values correspond to COLUMNS
        Y values correspond to ROWS
    """

    # Static lock used by all charts to ensure more than one chart isn't being plotted at the same time.
    plot_lock = threading.Lock()

    def __init__(self, x_vector: Sequence, y_vector: Sequence, z_matrix: np.array):
        # convert vectors into matrices (necessary operation in order to plot)
        assert matplotlib.get_backend() == "TkAgg"

        x = np.array(x_vector)
        y = np.array(y_vector)
        self.X, self.Y = np.meshgrid(x, y)
        self.Z = z_matrix

        self.axes = None
        self.figure = None

        # formatting specific fields
        self._x_label = None
        self._y_label = None
        self._z_label = None
        self._title_str = None

    def plot(self, figsize: Tuple[float, float] = None, include_contour: bool = False):
        """
        Plots the chart. The underlying figure stays hidden until the show() method is called.

        Parameters
        ----------
        figsize: Tuple[float, float]
            The figure size to draw the chart at in inches. This is a tuple of (width, height) passed directly
            to matplotlib's ``plot`` function. The values are expressed in inches.
        include_contour: bool
        """

        self._setup_axes_if_necessary(figsize)

        # Plot the surface.
        surf = self.axes.plot_surface(self.X, self.Y, self.Z, cmap='jet', rstride=1, cstride=1)

        if include_contour:
            self.axes.contour(self.X, self.Y, self.Z, zdir='x', offset=self.X.min(), cmap='coolwarm')
            self.axes.contour(self.X, self.Y, self.Z, zdir='y', offset=self.Y.max(), cmap='coolwarm')

        self.figure.colorbar(surf)
        self._apply_formatting()

    def show(self):
        """
        Shows the chart. It is necessary to call the plot function first.
        """
        self.figure.show()

    def close(self):
        """
        Closes the window containing the figure.
        """
        plt.close(self.figure)

    def set_axes_names(self, x_label: str = None, y_label: str = None, z_label: str = None):
        self._x_label = x_label
        self._y_label = y_label
        self._z_label = z_label

    def set_title(self, title_str: str):
        self._title_str = title_str

    def _apply_formatting(self):
        if self._x_label is not None:
            self.axes.set_xlabel(self._x_label)
        if self._y_label is not None:
            self.axes.set_ylabel(self._y_label)
        if self._z_label is not None:
            self.axes.set_zlabel(self._z_label)

        if self._title_str is not None:
            plt.title(self._title_str)

    def _setup_axes_if_necessary(self, figsize: Tuple[float, float] = None):
        if self.axes is None:
            figure = plt.figure(figsize=figsize)
            ax = figure.add_subplot(1, 1, 1, projection='3d')  # (nrows, ncols, axnum)
            ax.grid(True)
            self.axes = ax
            self.figure = figure
        if figsize is not None:
            # Make sure the specified figsize is set.
            self.axes.figure.set_size_inches(figsize[0], figsize[1])
