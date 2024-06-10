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
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union, Sequence

from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.db_connection_providers import DBConnectionProvider
from qf_lib.data_providers.sp_global.sp_field import SPField


class SPDAO(metaclass=ABCMeta):
    def __init__(self, db_connection_provider: DBConnectionProvider):
        self._db_connection_provider = db_connection_provider

    @property
    @abstractmethod
    def supported_fields(self) -> list[SPField]:
        raise NotImplementedError

    @abstractmethod
    def get_history(self, tickers: Union[SPTicker, Sequence[SPTicker]], fields: Union[SPField, Sequence[SPField]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = None, **kwargs) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        raise NotImplementedError

    @property
    @abstractmethod
    def _supported_tables(self) -> list[SPField]:
        raise NotImplementedError

    def _automap_tables(self):
        metadata = MetaData()
        metadata.reflect(self._db_connection_provider.engine, only=self._supported_tables)
        base = automap_base(metadata=metadata)
        base.prepare()
        for table in self._supported_tables:
            try:
                setattr(self, table, getattr(base.classes, table))
            except AttributeError:
                raise ValueError(f"Couldn't successfully reflect table {table}") from None
