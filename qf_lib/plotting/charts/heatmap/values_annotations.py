import numpy as np
import seaborn.utils as sb_utils

from qf_lib.plotting.charts.heatmap.heatmap_chart_decorator import HeatMapChartDecorator


class ValuesAnnotations(HeatMapChartDecorator):
    """ Adds annotations containing values for each square presented on the heat map. """
    def __init__(self, format_str='.2g', key=None, **plot_settings):
        """
        Parameters
        ----------
        format_str
            The format of the annotation showed inside of each element of the heat map
        key
            see: Chart.__init__#key
        plot_settings
            additional keyword arguments passed to the matplotlib's Axes.text() method
        """
        super().__init__(key)
        self._plot_settings = plot_settings
        self._format_str = format_str

    def decorate(self, chart: "HeatMapChart"):
        mesh = chart.color_mesh_
        ax = chart.axes

        x_locs, y_locs = np.meshgrid(ax.get_xticks(), ax.get_yticks())
        values = mesh.get_array()
        mesh_facecolors = mesh.get_facecolors()

        for x, y, value, mesh_face_color in zip(x_locs.flat, y_locs.flat, values, mesh_facecolors):
            annotation = ("{:" + self._format_str + "}").format(value)

            text_color = self.get_text_color(mesh_face_color)
            plot_settings = dict(color=text_color, ha="center", va="center")
            plot_settings.update(self._plot_settings)
            ax.text(x, y, annotation, **plot_settings)

    def get_text_color(self, background_color):
        luminance = sb_utils.relative_luminance(background_color)
        text_color = ".15" if luminance > .408 else "w"
        return text_color
