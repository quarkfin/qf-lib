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
from enum import Enum
from typing import Mapping, Sequence

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.common_start_and_end import get_common_start_and_end
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.bloomberg.bloomberg_data_provider import BloombergDataProvider
from qf_lib.portfolio_construction.portfolio_models.equal_risk_contribution_portfolio import \
    EqualRiskContributionPortfolio
from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio


class ChangeDirection(Enum):
    RISING = 1
    """Rising"""
    FALLING = 2
    """Failing"""


class RiskParityBoxes:
    def __init__(self, boxes_dict: Mapping[ChangeDirection, Mapping[ChangeDirection, SimpleReturnsSeries]]):
        self._boxes_dict = boxes_dict

    def get_series(self, growth: ChangeDirection, inflation: ChangeDirection) -> SimpleReturnsSeries:
        return self._boxes_dict[growth][inflation]

    def as_list(self) -> Sequence[SimpleReturnsSeries]:
        """
        Creates a list of series corresponding to risk parity boxes. Order of series:
        (growth=RISING, inflation=RISING), (growth=RISING, inflation=FALLING), (growth=FALLING, inflation=RISING),
        (growth=FALLING, inflation=FALLING).
        """
        list_of_series = []
        for growth in ChangeDirection:
            for inflation in ChangeDirection:
                series = self._boxes_dict[growth][inflation]
                list_of_series.append(series)

        return list_of_series

    @staticmethod
    def from_list(list_of_series: Sequence[SimpleReturnsSeries]) -> "RiskParityBoxes":
        """
        Create a RiskParityBoxes instance from a list of series. The order in the list must be the following:
        (growth=RISING, inflation=RISING), (growth=RISING, inflation=FALLING), (growth=FALLING, inflation=RISING),
        (growth=FALLING, inflation=FALLING).
        """
        series_iter = iter(list_of_series)
        growth_to_inflation_to_series = dict()
        for growth in ChangeDirection:
            inflation_to_series = dict()
            for inflation in ChangeDirection:
                series = next(series_iter)
                inflation_to_series[inflation] = series
            growth_to_inflation_to_series[growth] = inflation_to_series

        try:
            next(series_iter)
            raise ValueError("Got more series than expected: {:d}".format(len(list_of_series)))
        except StopIteration:
            pass  # this error was expected

        return RiskParityBoxes(growth_to_inflation_to_series)


class RiskParityBoxesFactory:
    """
    Makes timeseries for risk parity boxes.

    Parameters
    ----------
    bbg_data_provider: BloombergDataProvider
        reference to bloomberg data provider
    """

    def __init__(self, bbg_data_provider: BloombergDataProvider):
        self.bbg_data_provider = bbg_data_provider

        # index: growth, columns: inflation
        self.tickers_dict = self._create_tickers_dict()

        self.all_tickers = self._get_all_tickers(self.tickers_dict)

    def make_parity_boxes(self, start_date: datetime, end_date: datetime, frequency: Frequency = Frequency.DAILY) -> RiskParityBoxes:
        """
        Downloads the needed data and makes parity boxes. Each box is one series of returns (starting at the first
        date after start_date and ending at the end_date).
        """
        asset_rets_df = self._get_assets_data(end_date, start_date, frequency)

        # create a dict: growth -> inflation -> None
        boxes_df = dict()

        for growth in ChangeDirection:
            inflation_to_rets_dict = dict()
            for inflation in ChangeDirection:
                tickers = self.tickers_dict[growth][inflation]
                asset_rets_for_box_df = asset_rets_df.loc[:, tickers]
                boxes_rets = self._calculate_box(asset_rets_for_box_df)
                inflation_to_rets_dict[inflation] = boxes_rets

            boxes_df[growth] = inflation_to_rets_dict

        return RiskParityBoxes(boxes_df)

    @staticmethod
    def _create_tickers_dict():
        # growth -> inflatoin -> tickers
        tickers_dict = {
            ChangeDirection.RISING: {
                ChangeDirection.RISING: [
                    BloombergTicker("SPGSCITR Index"),  # Commodities (S&P GSCI Total Return CME)
                    BloombergTicker("MSBIERTR Index"),  # EM Debt (Morningstar Emerging Markets Corporate Bond Index TR)
                    BloombergTicker("XAU Curncy")  # Gold (XAUUSD Spot Exchange Rate - Price of 1 XAU in USD)
                ],
                ChangeDirection.FALLING: [
                    BloombergTicker("MXUS Index"),  # Equity USA (MSCI USA)
                    BloombergTicker("LQD US Equity")  # Credit (ISHARES IBOXX investment grade corporate bond etf)
                ]
            },
            ChangeDirection.FALLING: {
                ChangeDirection.RISING: [
                    # ILB (Bloomberg Barclays US Inflation Linked Bonds 1 to 10 Year TR)
                    BloombergTicker("BCIT3T Index"),
                    # Gold (XAUUSD Spot Exchange Rate - Price of 1 XAU in USD)
                    BloombergTicker("XAU Curncy")
                ],
                ChangeDirection.FALLING: [
                    BloombergTicker("IEF US Equity"),  # Gov bonds (7-10y treasury)
                    BloombergTicker("XAU Curncy")  # Gold (XAUUSD Spot Exchange Rate - Price of 1 XAU in USD)
                ]
            }
        }

        return tickers_dict

    @staticmethod
    def _get_all_tickers(tickers_dict):
        all_tickers = set()
        for inflation_to_tickers in tickers_dict.values():
            for tickers in inflation_to_tickers.values():
                all_tickers.update(tickers)

        return sorted(list(all_tickers))

    def _get_assets_data(self, end_date, start_date, frequency):
        # download data
        asset_prices_df = self.bbg_data_provider.get_price(self.all_tickers, PriceField.Close, start_date, end_date, frequency)
        asset_prices_df = cast_dataframe(asset_prices_df, output_type=PricesDataFrame)

        # trim
        common_start, common_end = get_common_start_and_end(asset_prices_df)
        trimmed_asset_prices_df = asset_prices_df.loc[common_start:common_end, :]  # type: PricesDataFrame

        # remove intermediate NaNs
        trimmed_asset_prices_df = trimmed_asset_prices_df.fillna(method='pad')  # forward fill

        # convert to simple returns
        assets_rets = trimmed_asset_prices_df.to_simple_returns()

        return assets_rets

    @staticmethod
    def _calculate_box(asset_returns_df: SimpleReturnsDataFrame) -> SimpleReturnsSeries:
        portfolio = EqualRiskContributionPortfolio(asset_returns_df.cov())
        weights = portfolio.get_weights()
        portfolio_rets, _ = Portfolio.constant_weights(asset_returns_df, weights)

        return portfolio_rets
