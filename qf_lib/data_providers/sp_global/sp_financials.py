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
from typing import Sequence
from sqlalchemy import or_

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.db_connection_providers import DBConnectionProvider
from qf_lib.data_providers.sp_global.sp_dao import SPDAO
from qf_lib.data_providers.sp_global.sp_field import SPField


class SPFinancials(SPDAO):
    def __init__(self, db_connection_provider: DBConnectionProvider):
        super().__init__(db_connection_provider)

    @property
    def supported_fields(self) -> list[SPField]:
        return [
            SPField.BookValPerSH,
            SPField.EPS,
            SPField.DvdPayOutRatio,
            SPField.Sales,
            SPField.ROE,
            SPField.RetCap,
            SPField.ProfMargin,
            SPField.Total_Debt_to_Capital,
            SPField.GrossMargin,
            SPField.CurrentRatio,
            SPField.EBITDA,
            SPField.NetDebtToEBITDA,
            SPField.TotalAssetTurnover,
            SPField.NetIncome
        ]

    def get_history(self, tickers: SPTicker | Sequence[SPTicker],
                    fields: SPField | Sequence[SPField],
                    start_date: datetime, end_date: datetime = None,
                    frequency: Frequency = None, period_type_id: str = '4') -> QFSeries | QFDataFrame | QFDataArray:

        actual_tickers_to_sp_id = {t: t.tradingitem_id for t in tickers}
        with self._db_connection_provider.Session.begin() as session:
            query = session \
                .query(self.ciqfininstance.filingdate, self.ciqfininstance.periodenddate,
                       self.ciqfincollectiondata.dataitemid, self.ciqfincollectiondata.dataitemvalue) \
                .filter(self.ciqfininstance.periodenddate >= start_date.date()) \
                .filter(self.ciqfininstance.periodenddate <= end_date.date()) \
                .filter(self.ciqfininstance.restatementtypeid == 2)
            # Get only the specified periodtypeid
            query = query \
                .join(self.ciqfinperiod, self.ciqfinperiod.financialperiodid ==
                      self.ciqfininstance.financialperiodid) \
                .join(self.ciqperiodtype, self.ciqperiodtype.periodtypeid == self.ciqfinperiod.periodtypeid) \
                .filter(self.ciqperiodtype.periodtypeid == period_type_id)
            # Get only relevant tickers
            query = query \
                .join(self.ciqsecurity, self.ciqsecurity.companyid == self.ciqfinperiod.companyid) \
                .join(self.ciqtradingitem, self.ciqtradingitem.securityid == self.ciqsecurity.securityid) \
                .filter(self.ciqtradingitem.tradingitemid.in_(actual_tickers_to_sp_id.values()))
            # Get only relevant fields
            query = query \
                .join(self.ciqfininstancetocollection,
                      self.ciqfininstancetocollection.financialinstanceid ==
                      self.ciqfininstance.financialinstanceid) \
                .join(self.ciqfincollection, self.ciqfincollection.financialcollectionid ==
                      self.ciqfininstancetocollection.financialcollectionid) \
                .join(self.ciqfincollectiondata, self.ciqfincollectiondata.financialcollectionid ==
                      self.ciqfincollection.financialcollectionid) \
                .filter(self.ciqfincollectiondata.dataitemid.in_(
                                                [field.value for field in fields]))

            tickers_with_currency = [
                actual_tickers_to_sp_id[ticker] for ticker in tickers if ticker.currency is not None]
            if sp_ticker.currency is not None:
                query = query.join(self.ciqcurrency, self.ciqcurrency.currencyid == self.ciqfincollection.currencyid)
                query = query.filter(
                    or_(self.ciqcurrency.isocode == sp_ticker.currency, self.ciqcurrency.isocode.is_(None)))
            else:
                self.logger.warning(f"Ticker {sp_ticker.as_string()} doesn't have any corresponding currency. "
                                    f"The fundamental data returned might contain various currency data items.")
            # Get currency
            query = query.join(self.ciqcurrency, self.ciqcurrency.currencyid ==
                               self.ciqfincollection.currencyid) \

        return

    @property
    def _supported_tables(self) -> list[str]:
        return [
            'ciqfininstance',
            'ciqfincollection',
            'ciqfincollectiondata',
            'ciqfinperiod',
            'ciqsecurity',
            'ciqtradingitem',
            'ciqperiodtype',
            'ciqfininstancetocollection',
            'ciqcurrency'
        ]