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

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.common.tickers.tickers import Ticker


class Signal(object):
    """
    Objects of this class are used in the portfolio construction process. They are returned by AlphaModels to
    determine the suggested trend direction as well as its strength

    Parameters
    ----------
    ticker: Ticker
        Ticker for which the signal was generated
    suggested_exposure: Exposure
        A value of type Exposure which describes the move suggested by a specific AlphaModel - SHORT, LONG or OUT
    fraction_at_risk: float
        A percentage value which determines the risk factor for an AlphaModel and a specified Ticker, may be used
        to calculate the position size.
        For example: Value of 0.02 means that we should place a Stop Loss 2% below the latest available
        price of the instrument. This value should always be positive
    confidence: float
        A float value in range [0;1] which describes the trust level for the AlphaModel in a current situation.
        By default set to 1.0 (maximum)
    expected_move: float
        A percentage value which determines an expected price change for the upcoming period, may by positive
        (uptrend) or negative (downtrend) and the range is unlimited
    alpha_model
        reference to the alpha model that generated the signal
    """

    def __init__(self, ticker: Ticker, suggested_exposure: Exposure, fraction_at_risk: float, confidence: float = 1.0,
                 expected_move: float = None, alpha_model=None):
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
