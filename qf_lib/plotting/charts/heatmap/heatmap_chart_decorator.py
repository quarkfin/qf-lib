import abc

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class HeatMapChartDecorator(ChartDecorator, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decorate(self, chart: "HeatMapChart"):
        pass
