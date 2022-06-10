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
from arch.univariate.volatility import VolatilityProcess

from qf_lib.common.utils.volatility.volatility_forecast import VolatilityForecast
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class RobustCovariance:
    """
    Creates a class used for vol forecasting and covariance matrix estimation
    NOTE: this method has a tendency to make decrease the volatility

    Parameters
    ----------
    simple_returns: QFDataFrame
        QFDataFrame of simple returns of the assets
    """

    def __init__(self, simple_returns: QFDataFrame):
        self.returns = simple_returns

    def calculate_covariance(self, vol_process: VolatilityProcess, horizon: int, method: str = 'analytic') -> QFDataFrame:
        """
        Calculates the covariance matrix using foretasted volatility for each asset and
        rank correlation between the assets. Covariance matrix contains NOT annualised values.
        They are expressed in the frequency of the input returns

        Parameters
        -----------
        vol_process: VolatilityProcess
            volatility proces used for forecats calculation. For example EGARCH(p=p, o=o, q=q)
        horizon: int
            horizon for the volatility forecast. It is expressed in the frequency of the returns provided
        method (optional): str
            method of the volatility forecast calculation. Possible: 'analytic', 'simulation' or 'bootstrap'
            'analytic' is the fastest but is not available for EGARCH and possibly some other models.
            For details check arch documentation

        Returns
        ----------
        QFDataFrame
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
