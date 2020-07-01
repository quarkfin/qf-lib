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

from typing import Callable

from qf_lib.containers.series.qf_series import QFSeries


def ta_series(func: Callable, *args, **kwargs) -> QFSeries:
    """
    Function created to allow using TA-Lib functions with QFSeries.

    Parameters
    ----------
    func
        talib function: for example talib.MA
    args
        time series arguments to the function. They are all passed as QFSeries.
        for example: 'close' or 'high, low, close' where each argument is a QFSeries.
    kwargs
        additional arguments to the function. for example: 'timeperiod=10' or 'timeperiod=timeperiod, matype=i'.
        All additional arguments have to be passed as keyword arguments.

    Returns
    -------
    QFSeries
        Output from the talib function encapsulated in a QFSeries
    """

    series_list = list(map(lambda series: series.values, args))

    result = func(*series_list, **kwargs)
    result = QFSeries(index=args[0].index, data=result)
    return result
