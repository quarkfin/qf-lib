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

import numpy as np
from numpy import power, sqrt
from numpy.linalg import inv

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class BlackLitterman:
    """
    Creates an object allowing calculation of the distribution of the returns using Black Litterman model

    Parameters
    -----------
    hist_cov: QFDataFrame
        covariance matrix of historical excess returns of assets; should be annualized
    weights: QFSeries
        weights of assets in the market cap index
    sample_size: int
        number of simple returns used to estimate the historical covariance
    sharpe: float
        average sharpe ratio of the market (by default value of 0.5 is used)
    """

    def __init__(self, hist_cov: QFDataFrame, weights: QFSeries, sample_size: int, sharpe: float = 0.5):
        self.hist_cov = hist_cov
        self.weights = weights
        self.tau = self._caltulate_tau(sample_size)
        self.sharpe = sharpe

        # properties used in view implementation
        self._p = None
        self._q = None
        self._omega = None

    @property
    def P(self) -> np.array:
        """
        Matrix of views P.
        nr of rows = number of different views
        nr of columns = number of assets
        Example for 4 assets and 2 views:

        - (0, 1, 0, 0) means go long second asset
        - (0, 1, 0, -1) means go long second asset while shorting first asset
        """

        return self._p

    @property
    def Q(self) -> np.array:
        """
        Vector of expected performance Q. Also sometimes refered as vector v
        nr of rows = number of different views
        nr of columns = 1
        For example:
        - [0.10]
        - [0.03]
        means that we have two views and we expect to realise 10% above risk free rate on first view and 3% on second
        """
        return self._q

    @property
    def Omega(self) -> np.array:
        """
        Matrix of variance of the views
        Matrix is square and diagonal. Each value Omega[i,i] corresponds to the variance of a specific view
        nr of rows = number of different views
        nr of columns = number of different views
        For example:
        - (0.0001, 0.0000) means we expect volatility of the first view to be sqrt(0.0001) = 0.01 = 1%
        - (0.0000, 0.0025) means we expect volatility of the first view to be sqrt(0.0025) = 0.05 = 5%
        NOTE: self._omega is stored as horizontal vector. Values are copied on diagonal
        """
        if self._omega is not None:
            N = self._omega.size
            omega = np.identity(N)
            for i in range(N):
                omega[i, i] = self._omega[i]
            return omega
        return None

    def add_absolute_view(self, asset_index: int, outperformance: float, view_vol: float):
        """
        Adds a new view that will be taken into account in calculating the posterior

        Parameters
        -------------
        short_asset_index: int
            index of the asset that we expect to outperform the market (indexing starts at 0)
        outperformance: float
            how much are we expecting one asset to outperform the market
        view_vol: float
            volatility of the view.
            This is the measure of a standard deviation of the outperformance value.
            For example: 0.02 means that the real outperformance will be
            provided outperformance +- 2% within one standard deviation confidence interval.
        """
        new_p_row = np.zeros((1, self.weights.size))
        new_p_row[0, asset_index] = 1
        new_q_elem = np.ones((1, 1)) * outperformance
        new_omega_elem = np.ones(1) * view_vol * view_vol  # Omega corresponds to variance of view so use the vol^2
        self._update_views(new_p_row, new_q_elem, new_omega_elem)

    def add_relative_view(self, outperforming_asset_index: int, underperforming_asset_index: int,
                          outperformance: float, view_vol: float):
        """
        Adds a new view that will be taken into account in calculating the posterior
        The investor believs that outperforming_asset will outperform the underperforming_asset by outperformance
        with the volatility of the view of  view_vol

        Parameters
        ----------
        outperforming_asset_index: int
            index of the asset that you believe will outperform (indexing starts at 0)
        underperforming_asset_index: int
            index of the asset that you believe will underperform (indexing starts at 0)
        outperformance: float
            how much are we expecting one asset to outperform the other
        view_vol: float
            volatility of the outperformance.
            This is the measure of a standard deviation of the outperformance value.
            For example: 0.02 means that the real outperformance will be
            provided outperformance +- 2% within one standard deviation confidence interval.
        """
        new_p_row = np.zeros((1, self.weights.size))
        new_p_row[0, outperforming_asset_index] = 1
        new_p_row[0, underperforming_asset_index] = -1
        new_q_elem = np.ones((1, 1)) * outperformance
        new_omega_elem = np.ones(1) * view_vol * view_vol  # Omega corresponds to variance of view so use the vol^2
        self._update_views(new_p_row, new_q_elem, new_omega_elem)

    def calculate_prior(self) -> Tuple[QFSeries, QFDataFrame]:
        """
        Function calculates the prior for the BL model:
        - prior_mean = lambda * hist_cov * market_cap_weights
        - prior_cov = tau * hist_cov

        Returns
        --------
        Tuple[QFSeries, QFDataFrame]
            Tuple(prior_mean, prior_cov)
        """

        lambda_ = self.calculate_lambda()
        prior_mean = lambda_ * self.hist_cov.dot(self.weights)
        prior_cov = self.tau * self.hist_cov
        return prior_mean, prior_cov

    def calculate_posterior(self) -> Tuple[QFSeries, QFDataFrame]:
        """
        Calculate shape of posterior distribution including the views. It is calculated using a numerically stable formula
        posterior_mean = prior_mean + tau * hist_cov * P' * ( tau * P * hist_cov * P' + Omega)^(-1) * (Q - P * prior_mean)
        posterior_cov = (1 + tau) * hist_cov - tau^2 * hist_cov * P' * (tau * P * hist_cov * P' + Omega)^(-1) * P * hist_cov

        Returns
        --------
        Tuple[QFSeries, QFDataFrame]
        """

        prior_mean, prior_sigma = self.calculate_prior()

        if self.P is not None:
            # calculate the posterior according to the formula above
            inverse_mat = self.tau * self.P.dot(self.hist_cov).dot(self.P.T) + self.Omega
            inverse_mat = inv(inverse_mat)

            P_dot_mean = self.P.dot(prior_mean).reshape(self.Q.shape)  # P * prior_mean      with a correct shape.
            # for some reason numpy calculates [3x9] * [1x9] -> [1x3], but it should be [3x1] instead !!!

            posterior_mean_update = self.tau * self.hist_cov.dot(self.P.T).dot(inverse_mat).dot(self.Q - P_dot_mean)
            posterior_mean_update = posterior_mean_update.squeeze()

            posterior_cov_update = power(self.tau, 2) * self.hist_cov.dot(
                self.P.T.dot(inverse_mat).dot(self.P).dot(self.hist_cov))
            # set the column names that disappeared  in the calculation
            posterior_cov_update.columns = posterior_cov_update.index
        else:
            # There are no views.
            posterior_mean_update = 0
            posterior_cov_update = 0

        posterior_mean = prior_mean + posterior_mean_update
        posterior_cov = (1 + self.tau) * self.hist_cov - posterior_cov_update
        return posterior_mean, posterior_cov

    def _update_views(self, new_p_row, new_q_elem, new_omega_elem):
        if self.P is None:
            self._p = new_p_row
            self._q = new_q_elem
            self._omega = new_omega_elem
        else:
            self._p = np.concatenate((self._p, new_p_row), axis=0)
            self._q = np.concatenate((self._q, new_q_elem), axis=0)
            self._omega = np.concatenate((self._omega, new_omega_elem), axis=0)

    def calculate_lambda(self):
        """
        Calculates lambda corresponding to risk aversion in the formula:
        max(w):  w'R - lambda/2 * w' * Cov * w:

        lambda is calculated in the followign way:
        lambda = sharpe_ratio_of_market / vol_of_market.
        """
        vol = self._calculate_volatility()
        lambda_ = self.sharpe / vol
        return lambda_

    def _calculate_volatility(self):
        # calculate historical volatility of the portfolio with market weights
        vol = sqrt(self.weights.dot(self.hist_cov.dot(self.weights.T)))
        return vol

    def _caltulate_tau(self, len_of_returns: int):
        """
        In many implementations it approximated by  1 / nr of observations, which corresponds to standard error
        That is the error of estimation of the covariance matrix

        Parameters
        -----------
        len_of_returns: int
            number of returns used to calculate the historical covariance matrix

        Returns
        --------
        float
            coefficient of uncertainty in the prior estimate of the mean
        """

        return 1 / len_of_returns

    def print(self):
        print("=====> VOL")
        print(self._calculate_volatility())
        print("=====> TAU")
        print(self.tau)
        print("=====> P")
        print(self.P)
        print("=====> Q")
        print(self.Q)
        print("=====> OMEGA")
        print(self.Omega)
