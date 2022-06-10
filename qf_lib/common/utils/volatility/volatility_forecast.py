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

from arch.univariate import ConstantMean, Normal
from arch.univariate.volatility import VolatilityProcess

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.qf_series import QFSeries


class VolatilityForecast:
    """
    Creates class used for vol forecasting: describes the volatility forecast configuration as well as the input
    and output data (output is created and assigned by calling one of the class methods).

    An instance of this class should describe one specific forecast and store its parameters.
    Parameters should NOT be modified after calling one of the calculation methods (only one call is allowed)

    Parameters
    ----------
    returns_tms: QFSeries
        series of returns of the asset
    vol_process: VolatilityProcess
        volatility process used for forecasting. For example EGARCH(p=p, o=o, q=q)
    horizon: str
        horizon for the volatility forecast. It is expressed in the frequency of the returns provided
    method: int
        method of forecast calculation. Possible: 'analytic', 'simulation' or 'bootstrap'
        'analytic' is the fastest but is not available for EGARCH and possibly some other models.
        For details check arch documentation
    annualise: bool
        flag indicating whether the result is annualised; True by default
    frequency: Frequency
        if annualise is True, this should be the frequency of the returns timeseries that is provided as input;
        not used if annualise is False.

    """
    def __init__(self, returns_tms: QFSeries, vol_process: VolatilityProcess, method: str = 'analytic',
                 horizon: int = 1, annualise: bool = True, frequency: Frequency = Frequency.DAILY):
        self.vol_process = vol_process
        self.method = method
        self.horizon = horizon
        self.window_len = None  # will be assigned after calculate_timeseries() method call

        assert not annualise or frequency is not None
        self.annualise = annualise
        self.frequency = frequency

        self.returns_tms = returns_tms.to_log_returns()
        self.forecasted_volatility = None  # will be assigned after calling one of the calculation methods

    def calculate_timeseries(self, window_len: int, multiplier: int = 1) -> QFSeries:
        """
        Calculates volatility forecast for single asset. It is expressed in the frequency of returns.
        Value is calculated based on the configuration as in the object attributes. The result of the calculation
        is returned as well as assigned as self.forecasted_volatility object attribute.

        Parameters
        ----------
        window_len: int
            size of the rolling window, number of rows used as input data to calculate forecasted volatility
        multiplier: int
            ex. 100 (should be > 1)
            improves the optimization performance, as for very small values the results may be faulty;
            after optimization the results are scaled back (division by multiplier value)

        Returns
        -------
        QFSeries
            Timeseries of forecasted volatility.
        """

        assert self.forecasted_volatility is None, "The forecast was already calculated."
        assert window_len is not None, "For timeseries calculation the rolling window length must be specified."
        self.window_len = window_len
        assert multiplier >= 1

        returns_tms = self.returns_tms * multiplier
        volatility_tms = returns_tms.rolling_window(window_len, self._calculate_single_value)
        volatility_tms = volatility_tms.dropna()
        volatility_tms = volatility_tms / multiplier

        if self.annualise:
            volatility_tms = annualise_with_sqrt(volatility_tms, self.frequency)

        self.forecasted_volatility = volatility_tms
        return volatility_tms

    def calculate_single_forecast(self, multiplier: int = 1000) -> float:
        """
        Calculates volatility forecast for single asset. It is expressed in the frequency of returns.
        Value is calculated based on the configuration as in the object attributes. The result of the calculation
        is returned as well as assigned as self.forecasted_volatility object attribute.

        Parameters
        ----------
        multiplier: int
            ex. 100 (should be > 1)
            improves the optimization performance, as for very small values the results may be faulty;
            after optimization the results are scaled back (division by multiplier value)

        Returns
        -------
        float
            Forecasted value of the volatility.
        """

        assert self.forecasted_volatility is None, "The forecast was already calculated."
        assert multiplier >= 1

        returns_tms = self.returns_tms * multiplier
        volatility_value = self._calculate_single_value(returns_tms)
        volatility_value = volatility_value / multiplier

        if self.annualise:
            volatility_value = annualise_with_sqrt(volatility_value, self.frequency)

        self.forecasted_volatility = volatility_value
        return volatility_value

    def _calculate_single_value(self, returns: LogReturnsSeries) -> float:
        am = self._get_ARCH_model(returns, self.vol_process)
        res = am.fit(disp='off', show_warning=False)  # options={'maxiter': 10000, 'ftol': 1e-2})
        forecasts = res.forecast(horizon=self.horizon, method=self.method)
        column_str = 'h.{}'.format(self.horizon)  # take value for the selected horizon
        forecasts_series = forecasts.variance[column_str]
        # take the last value (most recent forecast)
        forecasted_value = forecasts_series[-1]
        # convert to volatility (if power=2, forecasted_value corresponds to variance, etc.)
        forecasted_vol = forecasted_value ** (1 / float(am.volatility.power))
        return forecasted_vol

    def _get_ARCH_model(self, returns: LogReturnsSeries, vol_process: VolatilityProcess):
        am = ConstantMean(returns)
        am.volatility = vol_process
        am.distribution = Normal()
        return am
