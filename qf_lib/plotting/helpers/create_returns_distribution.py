from matplotlib.ticker import FormatStrFormatter, MaxNLocator

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.charts.histogram_chart import HistogramChart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_locator_decorator import AxesLocatorDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_returns_distribution(returns: QFSeries, frequency: Frequency = Frequency.MONTHLY) -> HistogramChart:
    """
    Creates a new returns distribution histogram with the specified frequency.

    Parameters
    ----------
    returns
        The returns series to use in the histogram.
    frequency
        frequency of the returns after aggregation

    Returns
    -------
    A new ``HistogramChart`` instance.
    """
    colors = Chart.get_axes_colors()
    aggregate_returns = get_aggregate_returns(returns, frequency, multi_index=True).multiply(100)

    chart = HistogramChart(aggregate_returns)

    # Format the x-axis so that its labels are shown as a percentage.
    x_axis_formatter = FormatStrFormatter("%.0f%%")
    axes_formatter_decorator = AxesFormatterDecorator(x_major=x_axis_formatter, key="axes_formatter")
    chart.add_decorator(axes_formatter_decorator)
    # Only show whole numbers on the y-axis.
    y_axis_locator = MaxNLocator(integer=True)
    axes_locator_decorator = AxesLocatorDecorator(y_major=y_axis_locator, key="axes_locator")
    chart.add_decorator(axes_locator_decorator)

    # Add an average line.
    avg_line = VerticalLineDecorator(aggregate_returns.values.mean(), color=colors[1], key="average_line_decorator",
                                     linestyle="--", alpha=0.8)
    chart.add_decorator(avg_line)

    # Add a legend.
    legend = LegendDecorator(key="legend_decorator")
    legend.add_entry(avg_line, "Mean")
    chart.add_decorator(legend)

    # Add a title.
    title = TitleDecorator("Distribution of " + str(frequency).capitalize() + " Returns", key="title_decorator")
    chart.add_decorator(title)
    chart.add_decorator(AxesLabelDecorator("Returns", "Occurrences"))

    return chart
