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

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class RiskContributionAnalysis:
    """ Calculates risk contribution metrics. """

    @classmethod
    def get_risk_contribution(cls, factors_rets: SimpleReturnsDataFrame, weigths_of_assets: QFSeries,
                              portfolio_rets: SimpleReturnsSeries) -> QFSeries:
        """
        Calculates risk contribution of different factors to the portfolio. Risk is defined as volatility.
        Uses x-sigma-rho formula (MSCI Bara paper).

        Parameters
        ----------
        factors_rets
            dataframe consisted of returns for different assets
        weigths_of_assets
            series of weights of each asset. It's indexed with names of assets.
        portfolio_rets
            return of the whole portfolio

        Returns
        -------
        pandas.Series
            Series of risk contributions (one for each asset) to the portfolio. It's indexed with names of assets.
        """
        volatility_of_returns = factors_rets.std(axis=0)

        correlation_asset_portfolio = factors_rets.apply(lambda series: series.corr(portfolio_rets))

        risk_contribution = weigths_of_assets * volatility_of_returns * correlation_asset_portfolio

        normalized_risk_contribution_msci = risk_contribution / risk_contribution.sum()
        return normalized_risk_contribution_msci

    @classmethod
    def get_risk_contribution_optimised(
            cls, assets_rets: SimpleReturnsDataFrame, weights_of_assets: QFSeries) -> QFSeries:
        """
        Calculates risk contribution of each asset of the portfolio.

        Parameters
        ----------
        assets_rets
            returns of assets building the portfolio (each assets in a separate column)
        weights_of_assets
            Series of weights (one for each asset).  It's indexed with names of assets.

        Returns
        -------
        Series of risk contributions (one for each asset). It's indexed with names of assets
        """

        assets_covariance = assets_rets.cov()
        risk_contribution = cls._get_normalized_risk_contribution(assets_covariance, weights_of_assets)

        return risk_contribution

    @classmethod
    def get_distance_to_equal_risk_contrib(
            cls, assets_returns_covariance: QFDataFrame, weights_of_assets: QFSeries) -> float:
        """
        By minimising this function it is possible to calculate Equal Risk Contribution Portfolio. It has better
        numerical properties than simple approach  ( riskContribution - mean(riskContribution) )
        Details: http://www.thierry-roncalli.com/download/erc-slides.pdf

        Parameters
        ----------
        assets_returns_covariance
            covariance matrix for assets returns data frame
        weights_of_assets
            weight of each asset in the portfolio. It's indexed with names of assets.

        Returns
        -------
        L2 (euclidean) distance from equal risk distribution
        """
        risk_contributions = cls._get_normalized_risk_contribution(assets_returns_covariance, weights_of_assets)
        num_of_assets = len(weights_of_assets)

        # sum up all the squared differences
        distance = 0
        for i in range(0, num_of_assets - 1):
            for j in range(i + 1, num_of_assets):
                partial_diff = risk_contributions.iloc[i] - risk_contributions.iloc[j]
                distance += partial_diff ** 2

        return np.sqrt(distance)

    @classmethod
    def is_equal_risk_contribution(cls, returns_covariance: QFDataFrame, weights_of_assets: QFSeries) -> bool:
        """
        Tells whether each asset has an equal risk contribution to the portfolio.

        Parameters
        ----------
        returns_covariance
            DataFrame which is a covariance matrix. Columns and rows are both indexed with names of assets.
        weights_of_assets
            Series of weights (one weight for each asset). It's indexed with names of assets.

        Returns
        -------
        True if each asset has and equal risk contribution. False -- otherwise.
        """
        distance = cls.get_distance_to_equal_risk_contrib(returns_covariance, weights_of_assets)

        num_of_assets = len(weights_of_assets)
        distances_number = 0.5 * num_of_assets * (num_of_assets - 1)  # number of pairs between different risk contribs

        # "reverse operation" to distance_to_equal_risk_contrib
        mean_risk_contribution_distance = distance / np.sqrt(distances_number)

        return mean_risk_contribution_distance < 0.005  # max distance: 0.5%

    @classmethod
    def _get_normalized_risk_contribution(
            cls, assets_returns_covariance: QFDataFrame, weights_of_factors: QFSeries) -> QFSeries:
        raw_risk_contribution = weights_of_factors * (assets_returns_covariance.dot(weights_of_factors))
        normalized_risk_contrib = raw_risk_contribution / raw_risk_contribution.sum()
        return normalized_risk_contrib
