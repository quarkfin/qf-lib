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

import numpy as np

from qf_lib.containers.series.qf_series import QFSeries


def tail_events(benchmark_tms: QFSeries, examined_tms: QFSeries, tail_percentile: float) -> [QFSeries, QFSeries]:
    """
    Gets tail events of the benchmark and corresponding events in the examined timeseries. Both benchmark_tms
    and examined_tms must be of the same length. Moreover, events on each position in both series must be corresponding.

    Example: for the tail_percentile = 16 all the events of the benchmark with values to the left from one standard
    deviation will be returned (along with corresponding events from examined_tms).

    Parameters
    ----------
    benchmark_tms: QFSeries
        timeseries corresponding to the benchmark
    examined_tms: QFSeries
        timeseries corresponding to the examined asset
    tail_percentile: float
        Percentile to compute. Must be a number from range [0,100]

    Returns
    -------
    Tuple[QFSeries, QFSeries]
        (benchmark_tail_tms, examined_tail_tms) - tail events of the benchmark, events from the
        examined series corresponding to the benchmark's tail events
    """
    assert benchmark_tms.index.equals(examined_tms.index)

    percentile = np.percentile(benchmark_tms, tail_percentile)

    indices_of_tail_events = benchmark_tms < percentile
    benchmark_tail_tms = benchmark_tms[indices_of_tail_events]
    examined_tail_tms = examined_tms[indices_of_tail_events]

    return benchmark_tail_tms, examined_tail_tms
