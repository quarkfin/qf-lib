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
from datetime import datetime
from typing import Optional

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.common.tickers.tickers import Ticker


class Signal:
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
    last_available_price: Optional[float]
        The last price that was available at the time of generating the signal
    creation_time: datetime
        time when the signal was created
    confidence: float
        A float value in range [0;1] which describes the trust level for the AlphaModel in a current situation.
        By default set to 1.0 (maximum)
    expected_move: float
        A percentage value which determines an expected price change for the upcoming period, may by positive
        (uptrend) or negative (downtrend) and the range is unlimited
    symbol: Optional[str]
        Symbol of the ticker (if None, the default value would be computed as the property ticker of the ticker).
        E.g. for BloombergTicker("Example Equity") the symbol should be simply equal to "Example Equity" (so there
        is no need to provide it). However, in case of e.g. BloombergFutureTicker("Example", "Example{} Equity", 1, 1)
        the symbol should point to the specific ticker that was used to generate the signal, e.g. "ExampleZ9 Equity".
        With ticker + symbol fields we are always able to track the exact ticker and contract that were used to generate
        a signal.
    alpha_model: "AlphaModel"
        reference to the alpha model that generated the signal
    """

    def __init__(self, ticker: Ticker, suggested_exposure: Exposure, fraction_at_risk: float,
                 last_available_price: float, creation_time: datetime, confidence: float = 1.0,
                 expected_move: Optional[float] = None, symbol: Optional[str] = None, alpha_model=None):
        self.ticker = ticker
        self.symbol = symbol if symbol is not None else ticker.ticker
        self.suggested_exposure = suggested_exposure
        self.last_available_price = last_available_price
        self.creation_time = creation_time
        self.confidence = confidence
        self.expected_move = expected_move
        self.fraction_at_risk = fraction_at_risk
        self.alpha_model = alpha_model

    def __eq__(self, other):
        if other is self:
            return True

        if not isinstance(other, Signal):
            return False

        return (self.ticker, self.suggested_exposure, self.confidence, self.expected_move, self.fraction_at_risk,
                self.alpha_model) == (other.ticker, other.suggested_exposure, other.confidence, other.expected_move,
                                      other.fraction_at_risk, other.alpha_model)

    def __str__(self):
        return "Signal \n" \
               "\tTicker:             {} \n" \
               "\tSuggested Exposure: {} \n" \
               "\tConfidence:         {} \n" \
               "\tExpected Move:      {} \n" \
               "\tFraction at Risk:   {} \n" \
               "\tAlpha Model:        {}".format(self.ticker, self.suggested_exposure, self.confidence,
                                                 self.expected_move, self.fraction_at_risk, str(self.alpha_model))
