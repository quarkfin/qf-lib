import numpy as np

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.line_decorators import HorizontalLineDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator


def create_holdings_chart(positions: QFDataFrame) -> LineChart:
    """
    Creates a line chart showing holdings per day based on the specified positions.

    Parameters
    ----------
    positions
        Positions as returned by the extract_rets_pos_txn_from_zipline function.

    Returns
    -------
    LineChart
    """
    # Based on:
    # https://github.com/quantopian/pyfolio/blob/5d63df4ca6e0ead83f4bebf9860732d37f532026/pyfolio/plotting.py#L323
    result = LineChart()

    # Perform some calculations.
    positions = positions.copy().drop("cash", axis="columns")
    holdings = positions.apply(lambda x: np.sum(x != 0), axis="columns")
    holdings_by_month = holdings.resample("1M").mean()

    holdings_decorator = DataElementDecorator(holdings, color="steelblue", linewidth=1.5)
    result.add_decorator(holdings_decorator)
    holdings_by_month_decorator = DataElementDecorator(holdings_by_month, color="orangered", alpha=0.5, linewidth=2)
    result.add_decorator(holdings_by_month_decorator)

    hline_decorator = HorizontalLineDecorator(holdings.values.mean(), linestyle="--")
    result.add_decorator(hline_decorator)

    legend = LegendDecorator()
    legend.add_entry(holdings_decorator, "Daily Holdings")
    legend.add_entry(holdings_by_month_decorator, "Average Daily Holdings, by month")
    legend.add_entry(hline_decorator, "Average Daily Holdings, net")
    result.add_decorator(legend)

    result.add_decorator(TitleDecorator("Holdings per Day"))
    result.add_decorator(AxesLabelDecorator(y_label="Amount of holdings per Day"))

    return result
