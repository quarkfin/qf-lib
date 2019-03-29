import numpy as np
from arch.univariate import ConstantMean, Normal
from arch.univariate.volatility import VolatilityProcess

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class VolatilityForecast(object):  # todo: make all other scripts compatible
    def __init__(self, returns_tms: SimpleReturnsSeries, vol_process: VolatilityProcess,
                 window_len: int = 20, horizon: int = 1, method: str = 'analytic',
                 annualise: bool = True, frequency: Frequency = Frequency.DAILY):
        """
        Creates class used for vol forecasting: describes the volatility forecast configuration as well as the input
        and output data (output is created and assigned by calling one of the class methods).

        An instance of this class should describe one specific forecast and store its parameters.
        Parameters should NOT be modified after calling calculate_timeseries() method.  # todo: find a way to prevent it

        Parameters
        ----------
        returns_tms
            series of simple returns of the asset
        vol_process
            volatility process used for forecasting. For example EGARCH(p=p, o=o, q=q)
        window_len
            number of rows used as input data to calculate forecasted volatility
        horizon
            horizon for the volatility forecast. It is expressed in the frequency of the returns provided
        method
            method of forecast calculation. Possible: 'analytic', 'simulation' or 'bootstrap'
            'analytic' is the fastest but is not available for EGARCH and possibly some other models.
            For details check arch documentation
        annualise
            flag indicating whether the result is annualised; True by default
        frequency
            if annualise is True, this should be the frequency of the returns timeseries that is provided as input;
            not used if annualise is False.

        """
        self.vol_process = vol_process
        self.window_len = window_len
        self.horizon = horizon
        self.method = method

        assert not annualise or frequency is not None
        self.annualise = annualise
        self.frequency = frequency

        self.returns_tms = returns_tms
        self.forecasted_volatility = None  # will be assigned in the calculate_timeseries() method

    def calculate_timeseries(self) -> QFSeries:
        """
        Calculates volatility forecast for single asset. It is expressed in the frequency of returns.
        Value is calculated based on the configuration as in the object attributes. The result of the calculation
        is returned as well as assigned as self.forecasted_volatility object attribute.

        Returns
        -------
        Forecasted value of the volatility.
        """

        assert self.forecasted_volatility is None, "Forecast can be calculated "

        # if multiply_by_const:  # todo
        #     returns = returns * multiplier

        volatility_tms = self.returns_tms.rolling_window(self.window_len, self._calculate_single_value)
        # volatility_tms = volatility_tms.shift(self.horizon)  # todo
        volatility_tms = volatility_tms.dropna()

        if self.annualise:
            volatility_tms = annualise_with_sqrt(volatility_tms, self.frequency)

        # if multiply_by_const:  # todo
        #     vol = vol / multiplier

        self.forecasted_volatility = volatility_tms
        return volatility_tms

    def _calculate_single_value(self, returns: SimpleReturnsSeries) -> float:
        """
        Calculates volatility forecast for single asset. Value is NOT annualised.
        It is expressed in the frequency of returns

        Parameters
        ----------
        returns
            series of simple returns of the asset

        Returns
        -------
        Forecasted value of the volatility (not annualised).
        """

        am = self._get_ARCH_model(returns, self.vol_process)
        res = am.fit(disp='off', show_warning=False)  # options={'maxiter': 10000, 'ftol': 1e-2})
        forecasts = res.forecast(horizon=self.horizon, method=self.method)
        column_str = 'h.{}'.format(self.horizon)  # take value for the selected horizon
        forecasts_series = forecasts.variance[column_str]
        # take the last value (most recent forecast)
        forecasted_value = forecasts_series[-1]
        # forecasted_value corresponds to variance. Convert to volatility
        forecasted_vol = np.sqrt(forecasted_value)  # todo: works only for power=2
        return forecasted_vol

    def _get_ARCH_model(self, returns: SimpleReturnsSeries, vol_process: VolatilityProcess):
        am = ConstantMean(returns)
        am.volatility = vol_process
        am.distribution = Normal()
        return am
