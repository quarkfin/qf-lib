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
from typing import List
from sklearn import linear_model
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.data_cleaner import DataCleaner
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.settings import Settings
from qf_lib.common.tickers.tickers import Ticker


class ExposureGenerator:
    """
    Class to generate exposure data based on provided regressors tickers

    Parameters
    ----------
    settings: Settings
        settings of the project
    data_provider: DataProvider
        DataProvider which provides data both for the tickers and regressors
    """
    def __init__(self, settings: Settings, data_provider: DataProvider):
        self.settings = settings
        self._data_provider = data_provider
        self.positions_history = None
        self.portfolio_nav_history = None
        self._sector_exposure_tickers = None
        self._factor_exposure_tickers = None
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def set_positions_history(self, positions_history: QFDataFrame, frequency: Frequency = Frequency.MONTHLY):
        """
        Sets the positions history with defined frequency sampling

        Parameters
        ----------
        positions_history: QFDataFrame
            QFDataFrame containing summary of the positions in the portfolio for each day
        frequency: Frequency
            Data frequency. Default: Frequency.MONTHLY
        """
        if frequency == Frequency.MONTHLY:
            self.positions_history = positions_history.resample('M').last()
        else:
            raise NotImplementedError("{} sampling is not implemented".format(frequency))

    def set_portfolio_nav_history(self, portfolio_eod_series: PricesSeries):
        """
        Sets the timeseries used to normalize exposure

        Parameters
        ----------
        portfolio_eod_series: PricesSeries
            timeseries of value of the portfolio expressed in currency units
        """
        self.portfolio_nav_history = portfolio_eod_series

    def set_sector_exposure_tickers(self, sector_exposure_tickers: List[Ticker]):
        """
        Sets sector exposure tickers

        Parameters
        ----------
        sector_exposure_tickers: List[Ticker]
            List of sector exposure tickers
        """
        self._sector_exposure_tickers = sector_exposure_tickers

    def set_factor_exposure_tickers(self, factor_exposure_tickers: List[Ticker]):
        """
        Sets factor exposure tickers

        Parameters
        ----------
        factor_exposure_tickers: List[Ticker]
            List of factor exposure tickers
        """
        self._factor_exposure_tickers = factor_exposure_tickers

    def get_sector_exposure(self, regression_len: int = 12):
        """
        Method used to generate sector-related coefficients of regressors defined in BacktestTradingSession

        Parameters
        ----------
        regression_len: int
            Length of history taken for each regression in months. It is used to determine the coefficients

        Returns
        -------
        QFDataFrame
            Contains computed coefficients for all available sector regressors
        """
        if self.positions_history is None or self.portfolio_nav_history is None:
            self.logger.info("History data not provided")
            return None
        if self._sector_exposure_tickers is None:
            self.logger.info("Sector exposure tickers not provided")
            return None
        sector_df = self._get_exposure(self._sector_exposure_tickers, regression_len)
        sector_df.name = "Sector exposure"
        return sector_df

    def get_factor_exposure(self, regression_len: int = 12):
        """
        Method used to generate factor-related coefficients of regressors defined in BacktestTradingSession

        Parameters
        ----------
        regression_len: int
            Length of history taken for each regression in months. It is used to determine the coefficients
        Returns
        -------
        QFDataFrame
            Contains computed coefficients for all available factor regressors
        """
        if self.positions_history is None or self.portfolio_nav_history is None:
            self.logger.info("History data not provided")
            return None
        if self._factor_exposure_tickers is None:
            self.logger.info("Factor exposure tickers not provided")
            return None
        factor_df = self._get_exposure(self._factor_exposure_tickers, regression_len)
        factor_df.name = "Factor exposure"
        return factor_df

    def _get_exposure(self, regressors_tickers: List, regression_len: int):
        df = QFDataFrame()
        for portfolio_date, positions in self.positions_history.iterrows():
            positions = positions.dropna()
            positions_tickers = positions.index.tolist()
            exposure = QFSeries([x.total_exposure for x in positions])
            portfolio_net_liquidation = self.portfolio_nav_history.asof(portfolio_date)
            positions_allocation = exposure / portfolio_net_liquidation
            from_date = portfolio_date - RelativeDelta(months=regression_len)
            coefficients, current_regressors_tickers = self._get_coefficients_and_current_regressors_tickers(
                regressors_tickers, positions_tickers, positions_allocation, from_date, portfolio_date)

            df = df.append(QFDataFrame({col: val for val, col in zip(coefficients, current_regressors_tickers)},
                                       index=[portfolio_date]))

        # remove missing regressors
        df = df.dropna(axis=1, how='all')
        return df

    def _get_coefficients_and_current_regressors_tickers(self, regressors_tickers: List[Ticker], positions_tickers: List[Ticker],
                                                         positions_allocation: QFSeries, from_date: datetime,
                                                         to_date: datetime):
        tickers = [*positions_tickers, *regressors_tickers]
        data = self._data_provider.get_price(tickers, PriceField.Close, from_date, to_date).to_simple_returns()
        dc = DataCleaner(data, 0.1)
        clean_data = dc.proxy_using_value(0)
        positions_returns = clean_data.reindex(columns=positions_tickers,
                                               fill_value=0)  # we expect the same dim as positions_allocation series
        regressors_returns = clean_data.reindex(columns=regressors_tickers).dropna(axis=1, how='all')
        portfolio_returns = positions_returns.dot(positions_allocation.values)
        return self._get_coefficients(regressors_returns, portfolio_returns), regressors_returns.columns

    def _get_coefficients(self, x: QFDataFrame, y: QFSeries):
        model = linear_model.LinearRegression()
        model.fit(x, y)
        return model.coef_
