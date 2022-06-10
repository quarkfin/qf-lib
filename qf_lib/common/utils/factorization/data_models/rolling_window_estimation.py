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

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class RollingWindowsEstimator:
    """
    Class for estimating parameters of rolling windows.
    """

    @classmethod
    def estimate_rolling_window_size(cls, container: Union[QFDataFrame, QFSeries]) -> int:
        """
        Estimates the size of the rolling window based on the number of samples.

        Parameters
        ----------
        container
            container with data analysed using rolling window

        Returns
        -------
        window_size
            the calculated size of the rolling window
        """
        num_of_samples = container.shape[0]

        if 12 <= num_of_samples < 20:
            window_size = 3
        elif 20 <= num_of_samples < 50:
            window_size = 6
        elif 50 <= num_of_samples < 120:
            window_size = 12
        elif 120 <= num_of_samples < 300:
            window_size = 30
        elif 300 <= num_of_samples < 500:
            window_size = 75
        elif 500 <= num_of_samples:
            window_size = 125
        else:
            raise ValueError("Too few samples to estimate a rolling window's size.")

        return window_size

    @classmethod
    def estimate_rolling_window_step(cls, container: Union[QFDataFrame, QFSeries]) -> int:
        """
        Estimates the step of the rolling window based on the number of samples.

        Parameters
        ----------
        container
            container with data analysed using rolling window

        Returns
        -------
        window_step
            the calculated step (shift) of the rolling window
        """
        num_of_samples = container.shape[0]

        if 12 <= num_of_samples < 120:
            step = 2
        elif 120 <= num_of_samples < 500:
            step = 10
        elif 500 <= num_of_samples < 1500:
            step = 20
        elif 1500 <= num_of_samples:
            step = 50
        else:
            raise ValueError("Too few samples to estimate a rolling window's size.")

        return step
