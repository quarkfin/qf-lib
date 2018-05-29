import threading
from collections import Sequence

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


class SurfaceChart3D(object):
    """
    Class for 3D charts
    """

    # Static lock used by all charts to ensure more than one chart isn't being plotted at the same time.
    plot_lock = threading.Lock()

    def __init__(self, x_vector: Sequence, y_vector: Sequence, z_matrix: np.array):
        """
        Creates a 3D surface chart

        Parameters
        ----------
        x_vector: vector corresponding to points on X axis
        y_vector: vector corresponding to points on Y axis
        z_matrix: matrix with values. The shape of the Z matrix has to be [len(Y), len(X)]
            X values correspond to COLUMNS
            Y values correspond to ROWS
        """

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

    def plot(self, figsize=None, include_contour=False):
        """
        Plots the chart. The underlying figure stays hidden until the show() method is called.

        Parameters
        ----------
        figsize: Tuple(float, float)
            The figure size to draw the chart at in inches. This is a tuple of (width, height) passed directly
            to matplotlib's ``plot`` function. The values are expressed in inches.
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

    def _setup_axes_if_necessary(self, figsize=None):
        if self.axes is None:
            figure = plt.figure(figsize=figsize)
            ax = figure.add_subplot(1, 1, 1, projection='3d')  # (nrows, ncols, axnum)
            ax.grid(True)
            self.axes = ax
            self.figure = figure
        if figsize is not None:
            # Make sure the specified figsize is set.
            self.axes.figure.set_size_inches(figsize[0], figsize[1])
