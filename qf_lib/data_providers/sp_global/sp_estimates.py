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
from typing import Sequence, Union

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.db_connection_providers import DBConnectionProvider
from qf_lib.data_providers.sp_global.sp_dao import SPDAO
from qf_lib.data_providers.sp_global.sp_field import SPField


class SPEstimates(SPDAO):
    def __init__(self, db_connection_provider: DBConnectionProvider):
        super().__init__(db_connection_provider)

    @property
    def supported_fields(self):
        return [SPField.LongTermGrowth, SPField.RevenueConsensus]

    @property
    def _supported_tables(self):
        return ['ciqEstimatePeriod', 'ciqestimatenumericdata', 'ciqcurrency', 'ciqestimateconsensus', 'ciqestimateperiod']

    def get_history(self, tickers: Union[SPTicker, Sequence[SPTicker]], fields: Union[SPField, Sequence[SPField]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = None, **kwargs) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        return
