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
from typing import Sequence, Optional

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.futures_model import FuturesModel
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


class RandomTradesAlphaModel(AlphaModel):
    """
    Alpha model which generated random trades for each ticker.

    Parameters
    ----------
    risk_estimation_factor
        float value which estimates the risk level of the specific AlphaModel. Corresponds to the level at which
        the stop-loss should be placed.
    data_provider: DataHandler
        DataHandler which provides data for the ticker.
    start_date: datetime
        first date considered in the returned series
    end_date: datetime
        last date considered in the returned series
    number_of_trades: int
        total number of trades, which should be generated between start_date and end_date
    time_in_the_market: float
        total time of the ticker in the market (should be a percentage value, between 0.0 and 1.0)
    exposure: Exposure
        the desired exposure (either short or long)
    frequency: Frequency
        frequency of the trading
    seed: Optional[int]
        seed used to make the scenarios deterministic
    """
    def __init__(self, risk_estimation_factor: float, data_provider: DataHandler, start_date: datetime,
                 end_date: datetime, tickers: Sequence[Ticker], number_of_trades: int, time_in_the_market: float,
                 exposure: Exposure = Exposure.LONG, frequency: Frequency = Frequency.DAILY, seed: Optional[int] = None):
        super().__init__(risk_estimation_factor, data_provider)

        self.timer = data_provider.timer
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency
        scenarios_generator = ScenariosGenerator()

        self.trading_scenarios = QFDataFrame(columns=tickers, data={
            ticker: scenarios_generator.make_exposure_scenarios(start_date, end_date, number_of_trades,
                                                                time_in_the_market, exposure, frequency,
                                                                seed and seed + i)
            for i, ticker in enumerate(tickers)
        })

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime,
                           frequency: Frequency) -> Exposure:
        try:
            current_time = current_time + RelativeDelta(hour=0, minute=0, second=0) \
                if frequency <= Frequency.DAILY else current_time
            return Exposure(self.trading_scenarios.loc[current_time, ticker])
        except KeyError:
            return current_exposure


class RandomTradesFuturesAlphaModel(FuturesModel):
    """
    Alpha model which generates random trades for each ticker and provides the integration with futures tickers.

    Parameters
    ----------
    risk_estimation_factor
        float value which estimates the risk level of the specific AlphaModel. Corresponds to the level at which
        the stop-loss should be placed.
    data_provider: DataHandler
        DataHandler which provides data for the ticker.
    start_date: datetime
        first date considered in the returned series
    end_date: datetime
        last date considered in the returned series
    number_of_trades: int
        total number of trades, which should be generated
    time_in_the_market: flaot
        total time of the ticker in the market (should be a percentage value, between 0.0 and 1.0)
    exposure: Exposure
        the desired exposure (either short or long)
    frequency: Frequency
        frequency of the trading
    seed: Optional[int]
        seed used to make the scenarios deterministic
    """
    def __init__(self, risk_estimation_factor: float, data_provider: DataHandler, start_date: datetime,
                 end_date: datetime, tickers: Sequence[Ticker], number_of_trades: int, time_in_the_market: float,
                 num_of_bars_needed: int = 180, exposure: Exposure = Exposure.LONG,
                 frequency: Frequency = Frequency.DAILY, seed: Optional[int] = None):
        super().__init__(num_of_bars_needed, risk_estimation_factor, data_provider)

        self.timer = data_provider.timer
        self.start_date = start_date
        self.end_date = end_date
        self.frequency = frequency

        scenarios_generator = ScenariosGenerator()

        self.trading_scenarios = QFDataFrame(columns=tickers, data={
            ticker: scenarios_generator.make_exposure_scenarios(start_date, end_date, number_of_trades,
                                                                time_in_the_market, exposure, frequency,
                                                                seed and seed + i)
            for i, ticker in enumerate(tickers)
        })

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime,
                           frequency: Frequency) -> Exposure:
        try:
            current_time = current_time + RelativeDelta(hour=0, minute=0, second=0) \
                if frequency <= Frequency.DAILY else current_time
            return Exposure(self.trading_scenarios.loc[current_time, ticker])
        except KeyError:
            return current_exposure
