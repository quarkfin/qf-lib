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

from typing import TypeVar

from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries

InputData = TypeVar('InputData', QFSeries, QFDataFrame)


def drawdown_tms(input_data: InputData, frequency: Frequency = None) -> InputData:
    """
    Calculates the timeseries of the same dates as prices_tms, which contains the drawdown value for each date.

    Parameters
    ----------

    input_data: QFSeries, QFDataFrame
        QF timeseries or multiple timeseries grouped into a DataFrame

    frequency: Frequency
        optional parameter that improves teh performance of the function as
        to_prices does not need to infer the frequency

    Returns
    -------
    QFSeries, QFDataFrame
        series of drawdowns (drawdown for each day). Drawdown for a given date is defined as the percentage difference
        between the the maximal price value up to the given date and the price value for that date.
    """
    prices_tms = input_data.to_prices(frequency=frequency)

    max_price_tms = prices_tms.cummax()
    drawdowns = 1 - prices_tms / max_price_tms

    if isinstance(input_data, QFSeries):
        drawdowns = cast_series(drawdowns, QFSeries)
    else:
        drawdowns = cast_dataframe(drawdowns, QFDataFrame)

    return drawdowns
