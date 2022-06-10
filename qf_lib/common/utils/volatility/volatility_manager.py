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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class VolatilityManager:
    """
    VolatilityManager uses rolling window to asses the historical volatility of a series.
    It is then using the results to find appropriate weights to be held in time
    in order to keep the volatility constant over time.

    Parameters
    ----------
    series: QFSeries
        series to be volatility managed
    frequency: Frequency
        frequency of the series that is passed
    """

    def __init__(self, series: QFSeries, frequency: Frequency = Frequency.DAILY):
        self.returns_tms = series.to_simple_returns()
        self.frequency = frequency

    def get_managed_series(self, vol_level: float, window_size: int = 20, lag: int = 1,
                           min_leverage: float = 0.25, max_leverage: float = 1) -> SimpleReturnsSeries:
        """
        Parameters
        ----------
        vol_level: float
            volatility level to be maintained expressed in number. for example 0.2 means 20% volatility
        window_size: int
            length of the window to asses the volatility
        lag: int
            how many periods do we need in order to implement the reallocation.
            1 means that already on close of the current day we adjust for the realised volatility of that day
        min_leverage: float
            min leverage the the function is allowed to apply
        max_leverage: float
            max leverage the the function is allowed to apply
        Returns
        -------
        SimpleReturnsSeries
            SimpleReturnsSeries containing returns of the series based on the input series passed in the constructor
            that is volatility managed according to the above parameters
        """

        def volatility_fun(window):
            return get_volatility(SimpleReturnsSeries(window), self.frequency)

        rolling_vol_tms = self.returns_tms.rolling_window(window_size=window_size, func=volatility_fun)

        # weights that we would need to make the series have constant volatility
        target_weights_tms = vol_level / rolling_vol_tms

        # shift the results to reflect the fact that adjustment can be made the next day the earliest
        target_weights_tms = target_weights_tms.shift(periods=lag).dropna()

        # apply constraints on leverage
        target_weights_tms[target_weights_tms > max_leverage] = max_leverage
        target_weights_tms[target_weights_tms < min_leverage] = min_leverage

        # apply the weights to the series of returns
        managed_returns_tms = self.returns_tms.loc[target_weights_tms.index]
        managed_returns_tms = managed_returns_tms * target_weights_tms

        skipped_part = self.returns_tms.iloc[:window_size]
        managed_returns_tms = skipped_part.append(managed_returns_tms, verify_integrity=True)

        return managed_returns_tms, target_weights_tms
