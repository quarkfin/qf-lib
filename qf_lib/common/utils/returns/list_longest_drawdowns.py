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

from datetime import datetime
from typing import Tuple, List

from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.series.qf_series import QFSeries


def list_longest_drawdowns(prices_tms: QFSeries, count: int) -> List[Tuple[datetime, datetime]]:
    """
    Analyses the specified series and finds the top ``count`` longest drawdowns.

    Returns
    -------
    Tuple[datetime, datetime]
        A list of 2-item tuples. The first tuple item contains the start date and the second the end date of the drawdown
        period.
    """
    result = []

    drawdown_timeseries = drawdown_tms(prices_tms)

    start_date = None

    for date, value in drawdown_timeseries.iteritems():
        if value == 0:
            if start_date is not None:
                result.append((start_date, date))
                start_date = None
        else:
            if start_date is None:
                start_date = date

    if start_date is not None:
        result.append((start_date, drawdown_timeseries.index[-1]))

    # Sort according to drawdown length.
    result.sort(key=lambda val: val[0] - val[1])
    return result[:count]
