from collections import Sequence

import numpy as np

from qf_lib.common.utils.returns.list_of_max_drawdowns import list_of_max_drawdowns
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.surface_chart_3d import SurfaceChart3D


def create_dd_probability_chart_3d(prices_tms: QFSeries) -> SurfaceChart3D:
    def count_dd_above_threshold(drawdown_series: Sequence, threshold: float):
        return sum(1 for dd in drawdown_series if dd > threshold)

    drawdowns, duration_of_drawdowns = list_of_max_drawdowns(prices_tms)
    bear_marker_definitions = np.arange(0.15, 0.55, 0.05)  # rows    -> will  be the Y axis
    all_examined_dds = np.arange(0.01, 0.20, 0.01)  # columns -> will  be the X axis
    percentage_ending_in_bear_market = np.ones((len(bear_marker_definitions), len(all_examined_dds))) * 100

    for i, bear_marker_definition in enumerate(bear_marker_definitions):
        nr_of_bear_markets = count_dd_above_threshold(drawdowns, bear_marker_definition)

        for j, examined_dd in enumerate(all_examined_dds):
            if examined_dd <= bear_marker_definition:
                number_of_dds_above = count_dd_above_threshold(drawdowns, examined_dd)
                percentage = nr_of_bear_markets / number_of_dds_above * 100
                percentage_ending_in_bear_market[i, j] = percentage

    chart = SurfaceChart3D(all_examined_dds, bear_marker_definitions, percentage_ending_in_bear_market)
    chart.set_axes_names('examined drawdown', 'bear market definition')
    chart.set_title('Percentage of drawdowns ending in bear market')

    return chart
