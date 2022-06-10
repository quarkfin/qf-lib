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

from abc import abstractmethod, ABCMeta
from datetime import datetime

from numpy import nan

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.average_true_range import average_true_range
from qf_lib.data_providers.data_provider import DataProvider


class AlphaModel(metaclass=ABCMeta):
    """
    Base class for all alpha models.

    Parameters
    ----------
    risk_estimation_factor
        float value which estimates the risk level of the specific AlphaModel. Corresponds to the level at which
        the stop-loss should be placed.
    data_provider: DataProvider
        DataProvider which provides data for the ticker. For the backtesting purposes, in order to avoid looking into
        the future, use DataHandler wrapper.
    """

    def __init__(self, risk_estimation_factor: float, data_provider: DataProvider):
        self.risk_estimation_factor = risk_estimation_factor
        self.data_provider = data_provider
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_signal(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime, frequency: Frequency) \
            -> Signal:
        """
        Returns the Signal calculated for a specific AlphaModel and a set of data for a specified Ticker

        Parameters
        ----------
        ticker: Ticker
            A ticker of an asset for which the Signal should be generated
        current_exposure: Exposure
            The actual exposure, based on which the AlphaModel should return its Signal. Can be different from previous
            Signal suggestions, but it should correspond with the current trading position
        current_time: datetime
            current time, which is afterwards recorded inside each of the Signals. The parameter is optional and if not
            provided, defaults to the current user time.
        frequency: Frequency
            frequency of data obtained by the data provider for signal calculation

        Returns
        -------
        Signal
            Signal being the suggestion for the next trading period
        """
        suggested_exposure = self.calculate_exposure(ticker, current_exposure, current_time, frequency)
        fraction_at_risk = self.calculate_fraction_at_risk(ticker, current_time, frequency)
        last_available_price = self.data_provider.get_last_available_price(ticker, frequency, current_time)

        signal = Signal(ticker, suggested_exposure, fraction_at_risk, last_available_price, current_time,
                        alpha_model=self)
        return signal

    @abstractmethod
    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime,
                           frequency: Frequency) -> Exposure:
        """
        Returns the expected Exposure, which is the key part of a generated Signal. Exposure suggests the trend
        direction for managing the trading position.
        Uses DataHandler passed when the AlphaModel (child) is initialized - all required data is provided in the child
        class.

        Parameters
        ----------
        ticker: Ticker
            Ticker for which suggested signal exposure is calculated.
        current_exposure: Exposure
            The actual exposure, based on which the AlphaModel should return its Signal. Can be different from previous
            Signal suggestions, but it should correspond with the current trading position
        current_time: datetime
            The time of the exposure calculation
        frequency: Frequency
            frequency of data obtained by the data provider for signal calculation
        """
        pass

    def calculate_fraction_at_risk(self, ticker: Ticker, current_time: datetime, frequency: Frequency) -> float:
        """
        Returns the float value which determines the risk factor for an AlphaModel and a specified Ticker,
        may be used to calculate the position size.

        For example: Value of 0.02 means that we should place a Stop Loss 2% below the latest available
        price of the instrument. This value should always be positive

        Parameters
        ----------
        ticker: Ticker
            Ticker for which the calculation should be made
        current_time: datetime
            The time of the fraction at risk calculation
        frequency: Frequency
            frequency of data obtained by the data provider for calculation

        Returns
        -------
        float
            percentage_at_risk value for an AlphaModel and a Ticker, calculated as Normalized Average True Range
            multiplied by the risk_estimation_factor, being a property of each AlphaModel:
            fraction_at_risk = ATR / last_close * risk_estimation_factor

        """
        time_period = 20
        return self._atr_fraction_at_risk(ticker, time_period, current_time, frequency)

    def _atr_fraction_at_risk(self, ticker, time_period, current_time, frequency):
        """
        Parameters
        ----------
        ticker
            Ticker for which the calculation should be made
        time_period
            time period in days for which the ATR is calculated
        current_time: datetime
            The time of the ART calculation
        frequency: Frequency
            frequency of data obtained by the data provider for calculation

        Returns
        -------
        float
            fraction_at_risk value for an AlphaModel and a Ticker, calculated as Normalized Average True Range
            multiplied by the risk_estimation_factor, being a property of each AlphaModel:
            fraction_at_risk = ATR / last_close * risk_estimation_factor
        """
        num_of_bars_needed = time_period + 1
        fields = [PriceField.High, PriceField.Low, PriceField.Close]
        try:
            prices_df = self.data_provider.historical_price(ticker, fields, num_of_bars_needed, current_time, frequency)
            fraction_at_risk = average_true_range(prices_df, normalized=True) * self.risk_estimation_factor
            return fraction_at_risk
        except ValueError:
            self.logger.error(f"Could not calculate the fraction_at_risk for the ticker {ticker.name}", exc_info=True)
            return nan

    def __str__(self):
        return self.__class__.__name__

    def __hash__(self):
        return hash((self.__class__.__name__, self.risk_estimation_factor,))
