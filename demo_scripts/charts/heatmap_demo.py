#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qf_lib.common.enums.axis import Axis
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.plotting.charts.heatmap.color_bar import ColorBar
from qf_lib.plotting.charts.heatmap.heatmap_chart import HeatMapChart
from qf_lib.plotting.charts.heatmap.values_annotations import ValuesAnnotations
from qf_lib.plotting.decorators.axis_tick_labels_decorator import AxisTickLabelsDecorator


def main():
    half_range = 0.5
    sample_values = np.random.rand(4, 5) * 2 * half_range - half_range
    rows = ['Stock A', 'Stock B', 'Stock C', 'Stock D']
    cols = ['2014', '2015', '2017', '2018', '2019']

    sample_df = QFDataFrame(data=sample_values, index=pd.Index(rows), columns=pd.Index(cols))
    chart = HeatMapChart(data=sample_df, min_value=-half_range, max_value=half_range)

    chart.add_decorator(AxisTickLabelsDecorator(labels=cols, axis=Axis.X, rotation='auto'))
    chart.add_decorator(AxisTickLabelsDecorator(labels=list(reversed(rows)), axis=Axis.Y))
    chart.add_decorator(ValuesAnnotations())
    chart.add_decorator(ColorBar())

    chart.plot()
    chart.figure.tight_layout()
    plt.show(block=True)


if __name__ == '__main__':
    main()
