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

from typing import List
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.common.tickers.tickers import Ticker


class ExposureSettings:
    """
    Class to combine data provider with exposure related functionality.

    Parameters
    ----------
    data_provider: DataProvider
        DataProvider object with data both for positions and regressors
    sector_exposure_tickers: List[Ticker]
        list of sector exposure tickers
    factor_exposure_tickers: List[Ticker]
        list of factor exposure tickers
    """
    def __init__(self, data_provider: DataProvider, sector_exposure_tickers: List[Ticker],
                 factor_exposure_tickers: List[Ticker]):
        self._data_provider = data_provider
        self._sector_exposure_tickers = sector_exposure_tickers
        self._factor_exposure_tickers = factor_exposure_tickers

    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider

    @property
    def sector_exposure_tickers(self) -> List[Ticker]:
        return self._sector_exposure_tickers

    @property
    def factor_exposure_tickers(self) -> List[Ticker]:
        return self._factor_exposure_tickers
