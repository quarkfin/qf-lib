from typing import List, Tuple

import seaborn as sns

from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


class DistChart(Chart):
    """
    Flexibly plot a univariate distribution of observations.

    For more details see: http://seaborn.pydata.org/generated/seaborn.distplot.html
    """

    def __init__(self):
        super().__init__(start_x=None, end_x=None)

    def plot(self, figsize: Tuple[float, float] = None):
        self._setup_axes_if_necessary(figsize)
        self._apply_decorators()
        self._adjust_style()

    def apply_data_element_decorators(self, data_element_decorators: List[DataElementDecorator]):
        for data_element in data_element_decorators:
            sns.distplot(data_element.data, ax=self.axes, **data_element.plot_settings)
