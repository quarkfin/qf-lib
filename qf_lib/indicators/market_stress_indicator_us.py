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

from datetime import datetime, timedelta
from math import floor
from typing import Sequence

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider


class MarketStressIndicator:
    """Calculates market stress indicator.

    Parameters
    -----------
    tickers: Sequence[Ticker]
        tickers building the stress indicator
    weights: Sequence[float]
        weights of the tickers in the indicator, do not need to sum to 1, will be normalized anyway
    data_provider: DataProvider
        data provider that will be used to access the history of the individual tickers
    """

    def __init__(self, tickers: Sequence[Ticker], weights: Sequence[float], data_provider: DataProvider):
        self.tickers = tickers
        self.weights = weights
        self.data_provider = data_provider

    def get_indicator(self, years_rolling: float, start_date: datetime, end_date: datetime, step: int = 1) -> QFSeries:
        """Returns the timeseries of the indicator.

        Parameters
        ------------
        years_rolling: float
            How may years of the history is used for to evaluate the single point
        start_date: datetime
            start date of the indicator returned
        end_date: datetime
            end date of the indicator returned
        step: int
            how many day is the rolling window shifted. It aslo tells us the step of the returned indicator in days

        Returns
        -------
        QFSeries
            Timeseries of market stress indicator
        """
        underlying_start_date = start_date - timedelta(days=floor(years_rolling * 365 * 1.1))
        data = self.data_provider.get_price(self.tickers, PriceField.Close, underlying_start_date, end_date)
        data = data.fillna(method='ffill')
        # data = data.dropna() # this line can be enabled but it will shift starting point by the years_rolling

        window_size = floor(252 * years_rolling)
        stress_indicator_tms = data.rolling_time_window(
            window_length=window_size, step=step, func=self._rolling_stress_indicator)

        stress_indicator_tms = stress_indicator_tms.loc[start_date:]
        return stress_indicator_tms

    def _rolling_stress_indicator(self, data_frame_window: QFDataFrame):
        zscore_df = QFDataFrame()
        for name, series in data_frame_window.items():
            zscore_df[name] = (series - series.mean()) / series.std()

        last_row = zscore_df.tail(1)
        result = last_row.dot(self.weights)  # produces a weighted sum of the z-scored values
        result = result[0] / sum(self.weights)  # result was a single element series, return the value only
        return result
