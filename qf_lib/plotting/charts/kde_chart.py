from typing import List

import seaborn as sns

from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


class KDEChart(Chart):
    """
    Fits and plots a univariate (bivariate TODO) kernel density estimate using Seaborn's kdeplot function.

    For more details see: https://stanford.edu/~mwaskom/software/seaborn/generated/seaborn.kdeplot.html
    """

    def __init__(self):
        super().__init__(start_x=None, end_x=None)

    def plot(self, figsize=None):
        self._setup_axes_if_necessary(figsize)
        self._apply_decorators()
        self._adjust_style()

    def apply_data_element_decorators(self, data_element_decorators: List[DataElementDecorator]):
        for data_element in data_element_decorators:
            plot_settings = data_element.plot_settings
            sns.kdeplot(data_element.data, ax=self.axes, **plot_settings)
