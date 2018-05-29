from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_gross_leverage_chart(gross_lev: QFSeries) -> LineChart:
    """
    Creates a line chart showing gross leverage based on the specified gross leverage values.

    Parameters
    ----------
    gross_lev: QFSeries
        Gross leverage as returned by the extract_rets_pos_txn_from_zipline function.

    Returns
    -------
    LineChart
    """
    result = LineChart()

    result.add_decorator(DataElementDecorator(gross_lev, linewidth=0.5, color="g"))

    result.add_decorator(HorizontalLineDecorator(gross_lev.mean(), color="g", linestyle="--", linewidth=3))

    result.add_decorator(TitleDecorator("Gross leverage"))
    result.add_decorator(AxesLabelDecorator(y_label="Gross leverage"))
    return result
