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

from typing import Tuple

from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries


class ReturnAttributionAnalysis:
    """
    Class used for calculating metrics of performance attribution.
    """

    @classmethod
    def get_factor_return_attribution(cls, fund_tms: QFSeries, fit_tms: QFSeries, regressors_df: QFDataFrame,
                                      coefficients: QFSeries, alpha: float) -> Tuple[QFSeries, float]:
        """
        Returns performance attribution for each factor in given regressors and also calculates the unexplained return.
        """
        fund_returns = fund_tms.to_simple_returns()
        regressors_returns = regressors_df.to_simple_returns()
        annualised_fund_return = cagr(fund_returns)
        annualised_fit_return = cagr(fit_tms)

        total_nav = fit_tms.to_prices(initial_price=1.0)

        def calc_factors_profit(series) -> float:
            factor_ret = regressors_returns.loc[:, series.name].values
            return coefficients.loc[series.name] * (total_nav[:-1].values * factor_ret).sum()

        factors_profits = regressors_returns.apply(calc_factors_profit)

        alpha_profit = total_nav[:-1].sum() * alpha
        total_profit = factors_profits.sum() + alpha_profit

        regressors_return_attribution = factors_profits * annualised_fit_return / total_profit
        regressors_return_attribution = cast_series(regressors_return_attribution, QFSeries)

        unexplained_return = annualised_fund_return - regressors_return_attribution.sum()

        return regressors_return_attribution, unexplained_return
