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

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Callable, Sequence, Union

from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import SPTicker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.data_providers.db_connection_providers import DBConnectionProvider
from qf_lib.data_providers.sp_global.sp_dao import SPDAO
from qf_lib.data_providers.sp_global.sp_field import SPDateType, SPField
from qf_lib.data_providers.helpers import normalize_data_array, tickers_dict_to_data_array


class SPFinancials(DataProvider, SPDAO):
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

    def _pivot_df(self, df: QFDataFrame, fields: Sequence[SPField], aggfunc: Union[Callable, str]) -> QFDataFrame:
        pivoted_df = pd.pivot_table(df, aggfunc=aggfunc, index=['tradingitemid', 'filingdate', 'periodenddate'],
                                    values='dataitemvalue', columns='dataitemid')
        return pivoted_df.rename(columns=self._map_str_to_spfield).reindex(fields, axis=1).reset_index()

    def _sort_and_drop_duplicates_by_datetype(self, df: QFDataFrame, sp_date_type: SPDateType) -> QFDataFrame:
        """Sorts and drop duplicates for the sp date types in the provided dataframe, the specified sp_date_type
        will be the new index of the dataframe and the date types columns will be dropped."""

        # Sort and drop duplicates
        df = df.sort_values(by=['tradingitemid', 'periodenddate', 'filingdate'],
                            ascending=[True, True, True])
        df = df.drop_duplicates(subset=['tradingitemid', 'periodenddate'], keep='first')
        # TODO - Always do this? or only when sp_date_type is filingdate
        df = df.drop_duplicates(subset=['tradingitemid', 'filingdate'], keep='last')

        # Create new index
        df.set_index(sp_date_type.value, inplace=True)
        df.index = pd.to_datetime(df.index.rename("dates"))
        return df.drop(['periodenddate', 'filingdate'], axis=1)

    def _filter_tickers_by_currency(self, df: QFDataFrame, tickers: Sequence[SPTicker],
                                    ticker_to_tid: dict[SPTicker, str]):
        tickers_to_currencies = {
            ticker_to_tid[ticker]: ticker.currency for ticker in tickers if ticker.currency is not None}
        if not len(tickers_to_currencies) == 0:
            df['ticker_currency'] = df['tradingitemid'].map(tickers_to_currencies)
            df = df[df['currencyid'] == df['ticker_currency']].drop(columns=['ticker_currency'])
        else:
            ...
            # TODO - Raise warning for tickers with no currency
        return df

    def get_history(self, tickers: SPTicker | Sequence[SPTicker],
                    fields: SPField | Sequence[SPField],
                    start_datetime: datetime, end_datetime: datetime = datetime.now(),
                    frequency: Frequency = Frequency.DAILY, period_type_id: str = '4',
                    sp_date_type: SPDateType = SPDateType.periodenddate) -> QFSeries | QFDataFrame | QFDataArray:

        """
        Parameters
        ----------
        tickers: SPTicker, Sequence[SPTicker]
            tickers for securities which should be retrieved
        fields: SPField, Sequence[SPField]
            fields from the Market Data dataset, that should be retrieved. To see available fields please refer to
            SPDataProvider(..).supported_fields.
        start_datetime: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_datetime: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used.
        frequency: Frequency
            frequency of the data. Data is fetched always on a daily basis and then if Frequency is lower than daily,
            it is being resampled.
        period_type_id: str
            period_type_id
        sp_date_type: SPDateType
            sp_date_type
        """

        if frequency != Frequency.DAILY:
            raise NotImplementedError("SPDataProvider get_history() supports currently only daily frequency.")

        fields, got_single_field = convert_to_list(fields, SPField)
        _unsupported_fields = [f for f in fields if f not in self.supported_fields]
        if any(_unsupported_fields):
            raise ValueError(f"Unsupported fields {_unsupported_fields}. To view the list of fields supported by "
                             f"{self.__class__.__name__} please refer to the output of supported_fields() function.")

        tickers, got_single_ticker = convert_to_list(tickers, SPTicker)
        ticker_to_tid = {t: t.tradingitem_id for t in tickers}
        start_datetime = self._adjust_start_date(start_datetime, frequency)
        got_single_date = self._got_single_date(start_datetime, end_datetime, frequency)

        with self._db_connection_provider.Session.begin() as session:
            query = session \
                .query(self.ciqtradingitem.tradingitemid,
                       self.ciqfininstance.filingdate,
                       self.ciqfininstance.periodenddate,
                       self.ciqfincollectiondata.dataitemid,
                       self.ciqfincollectiondata.dataitemvalue) \
                .filter(self.ciqfininstance.periodenddate >= start_datetime.date()) \
                .filter(self.ciqfininstance.periodenddate <= end_datetime.date()) \
                .filter(self.ciqfininstance.filingdate > self.ciqfininstance.periodenddate) \
                .filter(self.ciqfininstance.restatementtypeid == 2)  # TODO = What is this

            # Get only the specified periodtypeid
            query = query \
                .join(self.ciqfinperiod,
                      self.ciqfinperiod.financialperiodid == self.ciqfininstance.financialperiodid) \
                .join(self.ciqperiodtype,
                      self.ciqperiodtype.periodtypeid == self.ciqfinperiod.periodtypeid) \
                .filter(self.ciqperiodtype.periodtypeid == period_type_id)  # TODO - What is this value?

            # Get only relevant tickers
            query = query \
                .join(self.ciqsecurity,
                      self.ciqsecurity.companyid == self.ciqfinperiod.companyid) \
                .join(self.ciqtradingitem,
                      self.ciqtradingitem.securityid == self.ciqsecurity.securityid) \
                .filter(self.ciqtradingitem.tradingitemid.in_(ticker_to_tid.values()))

            # Get only relevant fields
            query = query \
                .join(self.ciqfininstancetocollection,
                      self.ciqfininstancetocollection.financialinstanceid == self.ciqfininstance.financialinstanceid) \
                .join(self.ciqfincollection, self.ciqfincollection.financialcollectionid ==
                      self.ciqfininstancetocollection.financialcollectionid) \
                .join(self.ciqfincollectiondata, self.ciqfincollectiondata.financialcollectionid ==
                      self.ciqfincollection.financialcollectionid) \
                .filter(self.ciqfincollectiondata.dataitemid.in_([field.value for field in fields]))

            # Get currency
            query = query \
                .join(self.ciqcurrency, self.ciqcurrency.currencyid == self.ciqfincollection.currencyid)

            query.order_by(self.ciqfininstance.periodenddate, self.ciqfininstance.filingdate,
                           self.ciqfincollectiondata.financialcollectionid)

            df = QFDataFrame(pd.read_sql(query.statement, con=session.bind)).replace([None], np.nan)

        df = self._filter_tickers_by_currency(df, tickers, ticker_to_tid)
        aggfunc = np.mean if sp_date_type == SPDateType.periodenddate else 'last'
        pivoted_df = self._pivot_df(df, fields, aggfunc)
        sorted_df = self._sort_and_drop_duplicates_by_datetype(pivoted_df, sp_date_type)

        # Create, normalize and return the data array
        tid_to_tickers = {tid: ticker for ticker, tid in ticker_to_tid.items()}
        tickers_dict = {
            tid_to_tickers[tid]: group.droplevel(0) for tid, group in sorted_df.groupby('tradingitemid')}
        data_array = tickers_dict_to_data_array(tickers_dict, tickers, fields)
        return normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field)

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
