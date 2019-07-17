from typing import Mapping, Any

from matplotlib import artist

from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class StemDecorator(ChartDecorator, SimpleLegendItem):
    """
    A simple decorator that displays a single series in a form of stems.
    """

    def __init__(self, series: QFSeries, key: str = None, marker_props: Mapping[str, Any] = None,
                 stemline_props: Mapping[str, Any] = None, baseline_props: Mapping[str, Any] = None):
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self._series = series
        self.marker_props = marker_props
        self.stemline_props = stemline_props
        self.baseline_props = baseline_props

    def decorate(self, chart: "Chart"):
        markerline, stemlines, baseline = chart.axes.stem(self._series.index.values, self._series.values)
        self.legend_artist = markerline

        if self.marker_props is not None:
            artist.setp(markerline, **self.marker_props)

        if self.stemline_props is not None:
            artist.setp(stemlines, **self.stemline_props)

        if self.baseline_props is not None:
            artist.setp(baseline, **self.baseline_props)
