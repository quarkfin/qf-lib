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
from unittest import TestCase

import numpy as np
import pandas as pd

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
    CalculateAndPlaceOrdersRegularEvent
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.strategies.alpha_model_strategy import AlphaModelStrategy
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker, Ticker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib.tests.integration_tests.backtesting.trading_session_for_tests import TradingSessionForTests


class TestAlphaModelPositionsLimit(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tickers = [
            BloombergTicker("MSFT US Equity"),
            BloombergTicker("AUDUSD Curncy"),
            BloombergFutureTicker("Heating Oil", "HO{} Comdty", 1, 1, 100),
        ]

        cls.prices_start_date = str_to_date("2020-01-02")
        cls.test_start_date = str_to_date("2020-01-03")
        cls.test_end_date = str_to_date("2020-01-09")

        cls.fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]
        cls.frequency = Frequency.DAILY

    def setUp(self):
        self.data_provider = self._mock_data_provider()

        self.ts = TradingSessionForTests(
            data_provider=self.data_provider,
            start_date=self.test_start_date,
            end_date=self.test_end_date,
            initial_cash=1000000,
            frequency=self.frequency
        )

        # --- Build the model --- #
        model = DummyAlphaModel(risk_estimation_factor=0.05, data_provider=self.ts.data_handler)
        self.model_tickers_dict = {model: self.tickers}

    def _mock_data_provider(self):
        dates_index = pd.bdate_range(start=self.prices_start_date, end=self.test_end_date)
        fields_number = len(self.fields)
        tickers = [
            BloombergTicker("MSFT US Equity"),
            BloombergTicker("AUDUSD Curncy"),
            BloombergTicker("HOZ9 Comdty", SecurityType.FUTURE, 100),  # Mock three contracts for Heating Oil
            BloombergTicker("HOF0 Comdty", SecurityType.FUTURE, 100),
            BloombergTicker("HOG0 Comdty", SecurityType.FUTURE, 100),
        ]

        # Mock price data array
        values = [
            [  # 02-01-2020
                # MSFT US Equity, AUDUSD Curncy, Heating Oil (3 contracts) prices
                [90], [90], [90], [90], [90]
            ], [  # 03-01-2020
                [95], [95], [85], [100], [85]
            ], [  # 06-01-2020
                [110], [100], [90], [100], [90]  # The Heating Oil contract will create an open position
            ], [  # 07-01-2020
                [90], [110], [95], [np.nan], [95]  # Rolling for Heating Oil occurs, new Heating Oil contract is bought
            ], [  # 08-01-2020
                [80], [120], [100], [100], [100]  # Previous Heating Oil is sold (there was no price on the 7th)
            ], [  # 09-01-2020
                [80], [120], [100], [100], [100]
            ],
        ]
        # Open, High, Low and Close prices are equal every day
        values = [[price * fields_number for price in day_prices] for day_prices in values]
        mocked_prices = QFDataArray.create(dates_index, tickers, self.fields, data=values)

        # Mock expiration dates
        exp_dates = {
            BloombergFutureTicker("Heating Oil", "HO{} Comdty", 1, 1, 100): QFDataFrame(
                data={
                    ExpirationDateField.FirstNotice: [
                        str_to_date("2019-12-01"), str_to_date("2020-01-07"), str_to_date("2020-02-03")
                    ],
                    ExpirationDateField.LastTradeableDate: [
                        str_to_date("2019-12-01"), str_to_date("2020-01-07"), str_to_date("2020-02-03")
                    ],
                },
                index=[BloombergTicker("HOZ9 Comdty", SecurityType.FUTURE, 100),
                       BloombergTicker("HOF0 Comdty", SecurityType.FUTURE, 100),
                       BloombergTicker("HOG0 Comdty", SecurityType.FUTURE, 100)]
            )
        }

        return PresetDataProvider(data=mocked_prices,
                                  exp_dates=exp_dates,
                                  start_date=str_to_date("2019-12-01"),
                                  end_date=self.test_end_date,
                                  frequency=self.frequency)

    def _get_assets_number_series(self, portfolio: Portfolio):
        """
        Returns series indexed by dates, containing the number of assets in the portfolio (where e.g. all Heating Oil
        contracts correspond to one asset)
        """
        positions_history = portfolio.positions_history()

        def map_to_traded_ticker(ticker):
            for fut_ticker in [t for t in self.tickers if isinstance(t, BloombergFutureTicker)]:
                if fut_ticker.belongs_to_family(ticker):
                    return fut_ticker
            return ticker

        assets_history = positions_history.rename(columns=map_to_traded_ticker)
        assets_history = assets_history.groupby(level=0, axis=1).apply(func=(
            lambda x: x.notna().any(axis=1).astype(int)
        ))

        return assets_history.sum(axis=1)

    def test_limiting_open_positions_1_position(self):
        max_open_positions = 1
        strategy = AlphaModelStrategy(self.ts, self.model_tickers_dict, use_stop_losses=False,
                                      max_open_positions=max_open_positions)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        self.ts.start_trading()

        number_of_assets = self._get_assets_number_series(self.ts.portfolio)
        number_of_assets_exceeded_the_limit = number_of_assets.where(number_of_assets > max_open_positions).any()

        self.assertFalse(number_of_assets_exceeded_the_limit)

    def test_limiting_open_positions_2_position(self):
        max_open_positions = 2
        strategy = AlphaModelStrategy(self.ts, self.model_tickers_dict, use_stop_losses=False,
                                      max_open_positions=max_open_positions)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        self.ts.start_trading()

        number_of_assets = self._get_assets_number_series(self.ts.portfolio)
        number_of_assets_exceeded_the_limit = number_of_assets.where(number_of_assets > max_open_positions).any()

        self.assertFalse(number_of_assets_exceeded_the_limit)


class DummyAlphaModel(AlphaModel):
    def __init__(self, risk_estimation_factor: float, data_provider: DataHandler):
        super().__init__(0.0, data_provider)

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure, current_time: datetime,
                           frequency: Frequency) -> Exposure:
        last_price = self.data_provider.get_last_available_price(ticker, frequency, current_time)

        if last_price >= 100.00:
            return Exposure.LONG
        elif last_price <= 80.00:
            return Exposure.OUT
        else:
            return current_exposure

    def calculate_fraction_at_risk(self, ticker: Ticker, current_time: datetime, frequency: Frequency):
        return self.risk_estimation_factor
