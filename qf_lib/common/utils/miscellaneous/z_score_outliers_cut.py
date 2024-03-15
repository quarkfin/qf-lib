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

from numpy import log
from qf_lib.containers.series.qf_series import QFSeries


def z_score_outliers_cut(series: QFSeries) -> QFSeries:
    """ Compute z-score for a series with logarithm the series and cutting std above 2 and -2 """
    # take a log to remove the outliers, then calculate z_score
    shift_value = 1 - series.min()
    log_series = log(series.astype(float) + shift_value)
    result = (log_series - log_series.mean()) / log_series.std()

    # constraint the limits at +-2
    result = result.clip(-2, 2)
    result = result.fillna(0.0)
    return result
