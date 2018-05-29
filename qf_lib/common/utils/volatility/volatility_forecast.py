import numpy as np
from arch.univariate import ConstantMean, Normal
from arch.univariate.volatility import VolatilityProcess

from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class VolatilityForecast(object):
    def __init__(self, returns: SimpleReturnsSeries):
        """
        Creates a class used for vol forecasting
        returns
            series of simple returns of the asset
        frequency
            frequency fo the returns in the series
        """
        self.returns = returns

    def calculate_vol_forecast(self, vol_process: VolatilityProcess, horizon: int, method: str) -> float:
        """
        Calculates volatility forecast for single asset. Value is NOT annualised.
        It is expressed in the frequency of returns

        vol_process
            volatility proces used for forecasting. For example EGARCH(p=p, o=o, q=q)
        horizon
            horizon for the volatility forecast. It is expressed in the frequency of the returns provided
        method
            method of forecast calculation. Possible: 'analytic', 'simulation' or 'bootstrap'
            'analytic' is the fastest but is not available for EGARCH and possibly some other models.
            For details check arch documentation

        :returns
        forecasted value of the volatility (not annualised)
        """
        am = self._get_ARCH_model(vol_process)
        res = am.fit(disp='off')
        forecasts = res.forecast(horizon=horizon, method=method)
        column_str = 'h.{}'.format(horizon)  # take value for the selected horizon
        forecasts_series = forecasts.variance[column_str]
        # take the last value (most recent forecast)
        forecasted_value = forecasts_series[-1]
        # forecasted_value corresponds to variance. Convert to volatility
        forecasted_vol = np.sqrt(forecasted_value)
        return forecasted_vol

    def _get_ARCH_model(self, vol_process: VolatilityProcess):
        am = ConstantMean(self.returns)
        am.volatility = vol_process
        am.distribution = Normal()
        return am