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


class InSampleReturnStats:
    """
    Stores values of stats used to build confidence interval (Cone Chart)

    Parameters
    ----------
    mean_log_ret: float
        mean log return expressed in the frequency of data samples (usually daily)
    std_of_log_ret: float
        std of log returns expressed in the frequency of data samples (usually daily)
    """

    def __init__(self, mean_log_ret: float = None, std_of_log_ret: float = None):
        self.mean_log_ret = mean_log_ret
        self.std_of_log_ret = std_of_log_ret

    def __str__(self):
        return "mean log return: {}, std of log returns: {}".format(self.mean_log_ret, self.std_of_log_ret)

    @staticmethod
    def get_stats_from_tms(series: QFSeries):
        log_ret_tms = series.to_log_returns()
        return InSampleReturnStats(log_ret_tms.mean(), log_ret_tms.std())
