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

import abc
from datetime import datetime
from typing import Optional, Dict

from joblib import Memory
from pandas import to_datetime

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.exceptions.not_enough_data_exception import NotEnoughDataException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.miscellaneous.average_true_range import average_true_range
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider


class FuturesModel(AlphaModel, metaclass=abc.ABCMeta):
    """
    Type of alpha model, which can be easily integrated with any type of Tickers (plain Ticker objects, as well as
    FutureTickers). It provides the functionality which allows to download the daily OHLCV prices data frame,
    regardless of ticker type (the get_data function).

    Parameters
    ----------
    num_of_bars_needed: int
        number of bars necessary to compute the exposure
    risk_estimation_factor: float
        float value which estimates the risk level of the specific AlphaModel. Corresponds to the level at which
        the stop-loss should be placed.
    data_provider: DataProvider
        DataProvider which provides data for the ticker. For backtesting purposes the Data Handler should be used.
    cache_path: Optional[str]
        path to a directory, which could be used by the model for caching purposes. If provided, the model will cache
        the outputs of get_data function.
    """

    def __init__(self, num_of_bars_needed: int, risk_estimation_factor: float, data_provider: DataProvider,
                 cache_path: Optional[str] = None):

        super().__init__(risk_estimation_factor, data_provider)

        # Precomputed futures chains
        self.futures_data: Dict[Ticker, FuturesChain] = {}
        if cache_path is not None:
            memory = Memory(cache_path, verbose=0)
            self.get_data = memory.cache(self.get_data, ignore=['self'])

        self.ticker_name_to_ticker = {}
        self.num_of_bars_needed = num_of_bars_needed
        self.num_of_bars_atr = num_of_bars_needed
        self.supported_frequency = Frequency.DAILY

    def get_signal(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime, frequency: Frequency)\
            -> Signal:
        assert self.supported_frequency == frequency, "Only frequency.DAILY is supported for the moment"
        self.ticker_name_to_ticker[ticker.name] = ticker
        suggested_exposure = self.calculate_exposure(ticker, current_exposure, current_time, frequency)
        fraction_at_risk = self.calculate_fraction_at_risk(ticker, current_time, frequency)

        specific_ticker = ticker.get_current_specific_ticker() if isinstance(ticker, FutureTicker) else ticker
        last_available_price = self.data_provider.get_last_available_price(specific_ticker, frequency, current_time)

        signal = Signal(ticker, suggested_exposure, fraction_at_risk, last_available_price, current_time,
                        alpha_model=self)
        return signal

    def get_data(self, ticker_str: str, end_date: datetime, frequency: Frequency, aggregate_volume: bool = False):
        """
        Downloads the OHCLV Prices data frame for the given ticker. In case of a FutureTicker, the function downloads
        the Futures Chain and applies backward adjustment to the prices.

        Parameters
        ----------
        ticker_str: str
            string representing the ticker for which the data should be downloaded
        end_date: datetime
            last date for the data to be fetched
        frequency: Frequency
            frequency of the data
        aggregate_volume: bool
            used only in case of future tickers - if set to True, the volume data would not be the volume for the
            given contract, but the volume aggregated across all contracts (for each day the volume will be simply
            the sum of all volumes of the existing contracts of the given future asset)
        """
        end_date = end_date + RelativeDelta(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - RelativeDelta(days=self.num_of_bars_needed + 50)
        ticker = self.ticker_name_to_ticker[ticker_str]
        if isinstance(ticker, FutureTicker):
            try:
                data_frame = self.futures_data[ticker].get_price(PriceField.ohlcv(), start_date, end_date, frequency)
            except KeyError:
                # Ticker was not preloaded or the FutureChain has expired
                self.futures_data[ticker] = FuturesChain(ticker, self.data_provider,
                                                         FuturesAdjustmentMethod.BACK_ADJUSTED)

                data_frame = self.futures_data[ticker].get_price(PriceField.ohlcv(), start_date, end_date, frequency)
            if aggregate_volume:
                data_frame[PriceField.Volume] = self._compute_aggregated_volume(ticker, start_date, end_date, frequency)

        else:
            data_frame = self.data_provider.get_price(ticker, PriceField.ohlcv(), start_date, end_date, frequency)

        data_frame = data_frame.dropna(how="all")
        return data_frame

    def _compute_aggregated_volume(self, ticker: FutureTicker, start_date: datetime, end_date: datetime,
                                   frequency: Frequency) -> Optional[QFSeries]:
        # Compute the TOTAL VOLUME (aggregated across contracts)
        futures_chain_tickers_df = self.data_provider.get_futures_chain_tickers(ticker,
                                                                                ExpirationDateField.all_dates())[ticker]
        # Get the minimum date
        futures_chain_tickers = futures_chain_tickers_df.min(axis=1)
        futures_chain_tickers = QFSeries(data=futures_chain_tickers.index, index=futures_chain_tickers.values)
        futures_chain_tickers.index = to_datetime(futures_chain_tickers.index)
        futures_chain_tickers = futures_chain_tickers.sort_index()

        futures_chain_tickers = futures_chain_tickers.loc[start_date:end_date + RelativeDelta(months=6)]
        all_specific_tickers = futures_chain_tickers.values.tolist()
        volume_df = self.data_provider.get_price(all_specific_tickers, PriceField.Volume, start_date, end_date,
                                                 frequency).dropna(axis=1, how="all").fillna(0)

        return volume_df.sum(axis=1) if not volume_df.empty else None

    def compute_atr(self, prices_df: PricesDataFrame):
        try:
            prices_df = prices_df[[PriceField.Close, PriceField.Open, PriceField.High, PriceField.Low]]
            prices_df = prices_df.dropna(how='all').fillna(method='ffill').dropna()
            #   Compute the ATR
            atr_values = average_true_range(prices_df.iloc[-self.num_of_bars_atr:], normalized=True)
        except Exception:
            raise NotEnoughDataException("Not enough data to compute the average true range")

        return atr_values

    def _atr_fraction_at_risk(self, ticker: Ticker, time_period, current_time, frequency):
        try:
            data_frame = self.get_data(ticker.name, current_time, frequency)
            atr_value = self.compute_atr(data_frame)
            return atr_value * self.risk_estimation_factor if is_finite_number(atr_value) else None
        except NotEnoughDataException:
            return None

    def __hash__(self):
        return hash((self.__class__.__name__, self.num_of_bars_needed, self.risk_estimation_factor))
