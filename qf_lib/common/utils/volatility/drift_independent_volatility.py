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

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class DriftIndependentVolatility:

    @staticmethod
    def get_volatility(
            ohlc: PricesDataFrame, frequency: Frequency = None, annualise: bool = True, alpha: float = None) -> float:
        """
        Implementation of the algorithm described in 'Drift Independent Volatility Estimation Based on High, Low,
        Open and Close Prices', developed by Dennis Yang and Qiang Zhang, published in June 2000 issue of Journal
        of Business. The new estimator has the following nice properties:

        - unbiased in the continuous limit,
        - independent of the drift,
        - dealing with opening price jumps in a consistent way,
        - smallest variance among all estimators with the similar properties.

        Parameters
        ----------
        ohlc: PricesDataFrame
            QFDataFrame consisting of four QFPricesSeries: open, high, low, close
        frequency: Frequency
            the frequency of samples in the returns series; it is only obligatory to specify frequency if the annualise
            parameter is set to True, which is a default value
        annualise: bool
            True if the volatility values should be annualised; False otherwise. If it is set to True, then it is obligatory
            to specify a frequency of the returns series.
        alpha: float
            expectation of u(u-c)+d(d-c) squared, values in range of (1.331, 1.5);
            authors of the algorithm suggest 1.34 in practice

        Returns
        -------
        float
            Drift Independent Volatility of type float
        """
        assert ohlc.num_of_rows >= 2
        assert not annualise or frequency is not None

        var_RS = DriftIndependentVolatility._rogers_satchell_variance(ohlc)
        var_O = DriftIndependentVolatility._open_variance(ohlc)
        var_C = DriftIndependentVolatility._close_variance(ohlc)
        k = DriftIndependentVolatility._k_factor(ohlc, alpha)

        variance = var_O + k * var_C + (1 - k) * var_RS
        volatility = np.sqrt(variance)

        if annualise:
            volatility = annualise_with_sqrt(volatility, frequency)

        return volatility

    @staticmethod
    def _rogers_satchell_variance(ohlc: QFDataFrame) -> float:
        """
        Variance estimator using the high, low, close prices found by Rogers and Satchell (1991) and Rogers, Satchell
        and Yoon (1994)
        described in equation (3)
        """
        u = DriftIndependentVolatility._get_normalized_high(ohlc).iloc[1:]
        d = DriftIndependentVolatility._get_normalized_low(ohlc).iloc[1:]
        c = DriftIndependentVolatility._get_normalized_close(ohlc).iloc[1:]
        n = ohlc.num_of_rows - 1

        var_RS = sum(u * (u - c) + d * (d - c)) / n
        return var_RS

    @staticmethod
    def _open_variance(ohlc: QFDataFrame) -> float:
        """
        Open price variance
        described in equation (8)
        """
        o = DriftIndependentVolatility._get_normalized_open(ohlc).iloc[1:]
        n = ohlc.num_of_rows - 1

        var_O = sum((o - o.mean()).pow(2)) / (n - 1)
        return var_O

    @staticmethod
    def _close_variance(ohlc: QFDataFrame) -> float:
        """
        Close price variance
        described in equation (8)
        """
        c = DriftIndependentVolatility._get_normalized_close(ohlc).iloc[1:]
        n = ohlc.num_of_rows - 1

        var_C = sum((c - c.mean()).pow(2)) / (n - 1)
        return var_C

    @staticmethod
    def _get_normalized_open(ohlc: QFDataFrame) -> QFSeries:
        """
        The normalized open price; notation adopted from the paper, similar to that used by Garman and Klass (1980)
        o = ln o1 - ln c0
        """
        o1 = ohlc[PriceField.Open]
        c0 = ohlc[PriceField.Close].shift(1)
        normalized_open = np.log(o1) - np.log(c0)
        return normalized_open

    @staticmethod
    def _get_normalized_high(ohlc: QFDataFrame) -> QFSeries:
        """
        The normalized high price; notation adopted from the paper, similar to that used by Garman and Klass (1980)
        u = ln h1 - ln o1
        """
        h1 = ohlc[PriceField.High]
        o1 = ohlc[PriceField.Open]
        normalized_high = np.log(h1) - np.log(o1)
        return normalized_high

    @staticmethod
    def _get_normalized_low(ohlc: QFDataFrame) -> QFSeries:
        """
        The normalized low price; notation adopted from the paper, similar to that used by Garman and Klass (1980)
        d = ln l1 - ln o1
        """
        l1 = ohlc[PriceField.Low]
        o1 = ohlc[PriceField.Open]
        normalized_low = np.log(l1) - np.log(o1)
        return normalized_low

    @staticmethod
    def _get_normalized_close(ohlc: QFDataFrame) -> QFSeries:
        """
        The normalized close price; notation adopted from the paper, similar to that used by Garman and Klass (1980)
        c = ln c1 - ln o1
        """
        c1 = ohlc[PriceField.Close]
        o1 = ohlc[PriceField.Open]
        normalized_close = np.log(c1) - np.log(o1)
        return normalized_close

    @staticmethod
    def _k_factor(ohlc: QFDataFrame, alpha) -> float:
        """
        Constant chosen to minimize the variance of the estimator var (get_volatility method)
        described in equation (10) and discussed in further paragraphs of the paper
        """
        n = ohlc.num_of_rows - 1
        if alpha is None:
            alpha = 1.34  # value suggested by the authors

        k = (alpha - 1) / (alpha + (n + 1) / (n - 1))
        return k
