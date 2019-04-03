from arch.univariate import ConstantMean, Normal
from arch.univariate.volatility import VolatilityProcess

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.containers.series.log_returns_series import LogReturnsSeries
from qf_lib.containers.series.qf_series import QFSeries


class VolatilityForecast(object):  # todo: make all other scripts compatible
    def __init__(self, returns_tms: QFSeries, vol_process: VolatilityProcess,
                 window_len: int = 20, horizon: int = 1, method: str = 'analytic',
                 annualise: bool = True, frequency: Frequency = Frequency.DAILY):
        """
        Creates class used for vol forecasting: describes the volatility forecast configuration as well as the input
        and output data (output is created and assigned by calling one of the class methods).

        An instance of this class should describe one specific forecast and store its parameters.
        Parameters should NOT be modified after calling calculate_timeseries() method.

        Parameters
        ----------
        returns_tms
            series of returns of the asset
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

        self.returns_tms = returns_tms.to_log_returns()
        self.forecasted_volatility = None  # will be assigned in the calculate_timeseries() method

    def calculate_timeseries(self, multiplier: int = 1) -> QFSeries:
        """
        Calculates volatility forecast for single asset. It is expressed in the frequency of returns.
        Value is calculated based on the configuration as in the object attributes. The result of the calculation
        is returned as well as assigned as self.forecasted_volatility object attribute.

        Returns
        -------
        Timeseries of forecasted volatility.
        """

        assert self.forecasted_volatility is None, "This forecast was already calculated."
        returns_tms = self.returns_tms * multiplier
        volatility_tms = returns_tms.rolling_window(self.window_len, self._calculate_single_value)
        volatility_tms = volatility_tms.dropna()
        volatility_tms = volatility_tms / multiplier

        if self.annualise:
            volatility_tms = annualise_with_sqrt(volatility_tms, self.frequency)

        self.forecasted_volatility = volatility_tms
        return volatility_tms

    def _calculate_single_value(self, returns: LogReturnsSeries) -> float:
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
        # convert to volatility (if power=2, forecasted_value corresponds to variance, etc.)
        forecasted_vol = forecasted_value ** (1 / float(am.volatility.power))
        return forecasted_vol

    def _get_ARCH_model(self, returns: LogReturnsSeries, vol_process: VolatilityProcess):
        am = ConstantMean(returns)
        am.volatility = vol_process
        am.distribution = Normal()
        return am
