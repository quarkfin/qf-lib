from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.common.tickers.tickers import Ticker


class Signal(object):
    """
    Objects of this class are used in the portfolio construction process. They are returned by AlphaModels to
    determine the suggested trend direction as well as its strength
    """

    def __init__(self, ticker: Ticker, suggested_exposure: Exposure, fraction_at_risk: float, confidence: float = 1.0,
                 expected_move: float = None, alpha_model=None):
        """
        Parameters
        ----------
        suggested_exposure
            A value of type Exposure which describes the move suggested by a specific AlphaModel - SHORT, LONG or OUT
        fraction_at_risk
            A percentage value which determines the risk factor for an AlphaModel and a specified Ticker, may be used
            to calculate the position size.
            For example: Value of 0.02 means that we should place a Stop Loss 2% below the latest available
            price of the instrument. This value should always be positive
        confidence
            A float value in range [0;1] which describes the trust level for the AlphaModel in a current situation.
            By default set to 1.0 (maximum)
        expected_move
            A percentage value which determines an expected price change for the upcoming period, may by positive
            (uptrend) or negative (downtrend) and the range is unlimited
        alpha_model
            reference to the alpha model that generated the signal

        """
        self.ticker = ticker
        self.suggested_exposure = suggested_exposure
        self.confidence = confidence
        self.expected_move = expected_move
        self.fraction_at_risk = fraction_at_risk
        self.alpha_model = alpha_model

    def __str__(self):
        return "Signal \n" \
               "\tTicker:             {} \n" \
               "\tSuggested Exposure: {} \n" \
               "\tConfidence:         {} \n" \
               "\tExpected Move:      {} \n" \
               "\tFraction at Risk:   {} \n" \
               "\tAlpha Model:        {}".format(self.ticker, self.suggested_exposure, self.confidence,
                                                 self.expected_move, self.fraction_at_risk, str(self.alpha_model))
