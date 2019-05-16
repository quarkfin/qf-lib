import numpy as np
from arch.univariate.volatility import VolatilityProcess
from pandas import DataFrame

from qf_lib.common.utils.volatility.volatility_forecast import VolatilityForecast


class RobustCovariance(object):

    def __init__(self, simple_returns: DataFrame):
        """
        Creates a class used for vol forecasting and covariance matrix estimation
        NOTE: this method has a tendency to make decrease the volatility

        simple_returns
            dataframe of simple returns of the assets

        """
        self.returns = simple_returns

    def calculate_covariance(self, vol_process: VolatilityProcess, horizon: int, method: str = 'analytic') -> DataFrame:
        """
        Calculates the covariance matrix using foretasted volatility for each asset and
        rank correlation between the assets. Covariance matrix contains NOT annualised values.
        They are expressed in the frequency of the input returns

        vol_process
            volatility proces used for forecats calculation. For example EGARCH(p=p, o=o, q=q)
        horizon
            horizon for the volatility forecast. It is expressed in the frequency of the returns provided
        method (optional)
            method of the volatility forecast calculation. Possible: 'analytic', 'simulation' or 'bootstrap'
            'analytic' is the fastest but is not available for EGARCH and possibly some other models.
            For details check arch documentation

        :returns
        cov_matrix of the assets.
        """
        vol_forecast_array = self._calculate_expected_volatilities(vol_process, horizon, method)
        # use spearman rank correlation instead of simple pearson correlation
        corr_matrix = self.returns.corr(method='spearman')
        cov_matrix = corr_matrix.copy()

        for i, _ in enumerate(vol_forecast_array):
            for j, _ in enumerate(vol_forecast_array):
                cov_matrix.iloc[i, j] = corr_matrix.iloc[i, j] * vol_forecast_array[i] * vol_forecast_array[j]
        return cov_matrix

    def _calculate_expected_volatilities(self, vol_process, horizon, method):
        vol_forecast_array = np.zeros(self.returns.shape[1])  # size = nr o assets
        for i, asset in enumerate(self.returns):
            asset_returns = self.returns[asset]
            vol_forecast = VolatilityForecast(asset_returns, vol_process, method, horizon, annualise=False)
            vol_forecast_array[i] = vol_forecast.calculate_single_forecast()
        return vol_forecast_array
