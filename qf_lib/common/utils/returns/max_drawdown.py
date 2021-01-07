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

from typing import Union


from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


def max_drawdown(input_data: Union[QFSeries, QFDataFrame], frequency: Frequency = None) -> Union[float, QFSeries]:
    """
    Finds maximal drawdown for the given timeseries of prices.

    Parameters
    ----------
    input_data: QFSeries, QFDataFrame
        timeseries of prices/returns
    frequency: Frequency
        optional parameter that improves teh performance of the function it is not need to infer the frequency

    Returns
    -------
        maximal drawdown for the given timeseries of prices expressed as the percentage value (e.g. 0.5 corresponds
        to the 50% drawdown)
    """
    return drawdown_tms(input_data, frequency=frequency).max()
