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
        Created line chart
    """
    result = LineChart()

    result.add_decorator(DataElementDecorator(gross_lev, linewidth=0.5, color="g"))

    result.add_decorator(HorizontalLineDecorator(gross_lev.mean(), color="g", linestyle="--", linewidth=3))

    result.add_decorator(TitleDecorator("Gross leverage"))
    result.add_decorator(AxesLabelDecorator(y_label="Gross leverage"))
    return result
