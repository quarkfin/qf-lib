import textwrap

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class TitleDecorator(ChartDecorator):
    def __init__(self, title: str, key=None):
        super().__init__(key)
        self._title = title

    def decorate(self, chart) -> None:
        axes = chart.axes

        # Word wrap to 60 characters.
        title = "\n".join(textwrap.wrap(self._title, width=60))

        axes.set_title(title)
