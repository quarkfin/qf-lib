from qf_lib.common.enums.axis import Axis
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.orientation import Orientation
from qf_lib.common.utils.returns.get_aggregate_returns import get_aggregate_returns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.axes_formatter_decorator import AxesFormatterDecorator, PercentageFormatter
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator
from qf_lib.plotting.decorators.bar_values_decorator import BarValuesDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import VerticalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_returns_bar_chart(returns: QFSeries, frequency: Frequency = Frequency.YEARLY) -> BarChart:
    """
    Constructs a new returns bar chart based on the returns specified. By default a new annual returns bar chart will
    be created.
    """
    colors = Chart.get_axes_colors()
    # Calculate data.
    aggregate_returns = get_aggregate_returns(returns, frequency, multi_index=True)
    data_series = QFSeries(aggregate_returns.sort_index(ascending=True))

    chart = BarChart(Orientation.Horizontal, align="center")
    chart.add_decorator(DataElementDecorator(data_series))
    chart.add_decorator(BarValuesDecorator(data_series))

    # Format the x-axis so that its labels are shown as a percentage.
    chart.add_decorator(AxesFormatterDecorator(x_major=PercentageFormatter()))

    # Format Y axis to make sure we have a tick for each year or 2 years
    if len(data_series) > 10:
        y_labels = data_series[data_series.index % 2 == 1].index
    else:
        y_labels = data_series.index
    chart.add_decorator(AxisTickLabelsDecorator(labels=y_labels, axis=Axis.Y, tick_values=y_labels))

    # Add an average line.
    avg_line = VerticalLineDecorator(
        aggregate_returns.values.mean(), color=colors[1], key="avg_line", linestyle="--", alpha=0.8)
    chart.add_decorator(avg_line)

    # Add a legend.
    legend = LegendDecorator(key="legend_decorator")
    legend.add_entry(avg_line, "Mean")
    chart.add_decorator(legend)

    # Add a title.
    title = TitleDecorator(str(frequency).capitalize() + " Returns", key="title_decorator")
    chart.add_decorator(title)
    chart.add_decorator(AxesLabelDecorator("Returns", "Year"))

    return chart
