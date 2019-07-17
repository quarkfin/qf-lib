from typing import Any

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class DataElementDecorator(ChartDecorator, SimpleLegendItem):
    """
    Wrapper for main data element used by a certain type of Chart. It stores the data container, plot settings
    and a handle for matplotlib's element representing the charted data (curve in LineChart, bars in BarChart etc.).
    """

    def __init__(self, data_container: object, key: str = None, use_secondary_axes: bool = False, **plot_settings: Any):
        """
        data_container
            container for the data to be charted (its type depends on the type of the chart)
        key
            Key is the identifier of the data element. It must be unique to each data element across the chart.
        use_secondary_axes
            Whether this data element should be plotted on the secondary axis.
        plot_settings:
            Additional settings for plotting the data element.
        """
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)
        self.data = data_container
        self.use_secondary_axes = use_secondary_axes
        self.plot_settings = plot_settings

    def decorate(self, chart: "Chart") -> None:
        # DataElementDecorator is being plotted in the Chart.apply_data_element_decorators together with all other
        # DataElementDecorators.
        pass
