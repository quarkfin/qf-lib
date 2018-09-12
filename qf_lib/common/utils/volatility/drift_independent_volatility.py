import numpy as np

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class DriftIndependentVolatility(object):

    @staticmethod
    def get_volatility(ohlc: QFDataFrame, alpha: float=None) -> QFSeries:
        """

        Implementation of the algorithm described in 'Drift Independent Volatility Estimation Based on High, Low,
        Open and Close Prices', developed by Dennis Yang and Qiang Zhang, published in June 2000 issue of Journal
        of Business. The new estimator has the following nice properties:
        (a) unbiased in the continuous limit,
        (b) independent of the drift,
        (c) dealing with opening price jumps in a consistent way,
        (d) smallest variance among all estimators with the similar properties.

        Parameters
        ----------
        ohlc:
            QFDataFrame consisting of four QFPricesSeries: open, high, low, close
        alpha:
            expectation of u(u-c)+d(d-c) squared, values in range of (1.331, 1.5);
            authors of the algorithm suggest 1.34 in practice

        Returns
        -------
        Drift Independent Volatility (annualized) in type QFSeries

        """
        var_RS = DriftIndependentVolatility._rogers_satchell_variance(ohlc)
        var_O = DriftIndependentVolatility._open_variance(ohlc)
        var_C = DriftIndependentVolatility._close_variance(ohlc)
        k = DriftIndependentVolatility._k_factor(ohlc, alpha)

        var = (var_O + k*var_C + (1-k)*var_RS) * 252
        vol = np.sqrt(var)
        return vol

    @staticmethod
    def _rogers_satchell_variance(ohlc: QFDataFrame) -> QFSeries:
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
    def _open_variance(ohlc: QFDataFrame) -> QFSeries:
        """
        Open price variance
        described in equation (8)
        """
        o = DriftIndependentVolatility._get_normalized_open(ohlc).iloc[1:]
        n = ohlc.num_of_rows - 1

        var_O = sum((o - o.mean()).pow(2)) / (n - 1)
        return var_O

    @staticmethod
    def _close_variance(ohlc: QFDataFrame) -> QFSeries:
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

        k = (alpha-1)/(alpha+(n+1)/(n-1))
        return k
