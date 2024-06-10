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
from typing import Sequence, Dict, Union, Set, Type, List

import numpy as np
import pandas as pd

from qf_lib.data_providers.db_connection_providers import DBConnectionProvider
from qf_lib.data_providers.sp_global.sp_dao import SPDAO
from qf_lib.data_providers.sp_global.sp_field import SPField

from qf_lib.common.utils.helpers import grouper
from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker, SPTicker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.helpers import tickers_dict_to_data_array, normalize_data_array
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


class SPDataProvider(AbstractPriceDataProvider, SPDAO):
    def __init__(self, db_connection_provider: DBConnectionProvider, use_adjusted_prices: bool = True,
                 exchange_rate_snap_id: int = 6):
        """
        Class to get Open, High, Low, Close and Volume from SP database

        Parameters
        ----------
        use_adjusted_prices: bool
            SP is not adjusting historical prices by default to all corporate actions.
            In order to adjust historical pricing to events like merges or spin-offs, one need to do it on his end.
            Current set up is adjusting pricing to match the best prices from BBG. By default True.
        exchange_rate_snap_id: int
            ID corresponding to the snapshot of the exchange rates used. Available values are:
                1	- Sydney Midday
                2	- Tokyo Midday
                3	- Sydney Close
                4	- Tokyo Close
                5	- London Midday
                6	- London Close
                7	- New York Midday
                8	- New York Close
            Default value is set to 6 (London Close).
        """
        AbstractPriceDataProvider.__init__(self)
        SPDAO.__init__(self, db_connection_provider)
        self.use_adjusted_prices = use_adjusted_prices

        if exchange_rate_snap_id not in range(1, 9):
            raise ValueError(f"Incorrect Snapshot ID {exchange_rate_snap_id}. Possible values are integers between "
                             f"1 and 8. Consult the documentation to see what each snapshot ID corresponds to.")
        self.exchange_rate_snap_id = exchange_rate_snap_id

    @property
    def supported_fields(self) -> list[SPField]:
        return [SPField.AskPrice, SPField.BidPrice, SPField.LowPrice, SPField.HighPrice, SPField.OpenPrice,
                SPField.ClosePrice, SPField.Volume, SPField.DivYield, SPField.Currency]

    def price_field_to_str_map(self) -> Dict[PriceField, SPField]:
        return {
            PriceField.Open: SPField.OpenPrice,
            PriceField.High: SPField.HighPrice,
            PriceField.Low: SPField.LowPrice,
            PriceField.Close: SPField.ClosePrice,
            PriceField.Volume: SPField.Volume
        }

    def get_history(self, tickers: Union[SPTicker, Sequence[SPTicker]], fields: Union[SPField, Sequence[SPField]],
                    start_datetime: datetime, end_datetime: datetime = datetime.now(),
                    frequency: Frequency = Frequency.DAILY, to_usd: bool = False, **kwargs):
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
        to_usd: bool
            flag indicating whether all pricing data should be converted to USD (by default False)

        Returns
        --------

        """

        # TODO add possibility to resample the frequency
        if frequency > Frequency.DAILY:
            raise NotImplementedError("SPDataProvider get_history() does not support intraday frequency.")

        tickers, got_single_ticker = convert_to_list(tickers, SPTicker)
        fields, got_single_field = convert_to_list(fields, SPField)
        start_datetime = self._adjust_start_date(start_datetime, frequency)
        got_single_date = self._got_single_date(start_datetime, end_datetime, frequency)

        # Dictionary mapping each of the tickers into a pandas DataFrame, which contains the values for each of the
        # requested fields. This dictionary is further converted into QFDataArray and normalized afterwards.
        tickers_data_dict = {}  # type: Dict[SPTicker, QFDataFrame]
        actual_tickers_to_sp_id = {t: t.tradingitem_id for t in tickers}
        fields_query = [(getattr(self.ciqpriceequity, field.value) / self.ciqexchangerate.priceclose
                         if to_usd and field in self._fields_to_adjust() else getattr(self.ciqpriceequity, field.value)
                         ).label(field.value) for field in fields]

        with self._db_connection_provider.Session.begin() as session:
            for ticker_group in grouper(1000, actual_tickers_to_sp_id.values()):
                historical_bars = session.query(self.ciqpriceequity.tradingitemid, self.ciqpriceequity.pricingdate,
                                                *fields_query) \
                    .join(self.ciqtradingitem, self.ciqtradingitem.tradingitemid == self.ciqpriceequity.tradingitemid) \
                    .join(self.ciqexchangerate, and_(self.ciqexchangerate.currencyid == self.ciqtradingitem.currencyid,
                                                     self.ciqexchangerate.pricedate == self.ciqpriceequity.pricingdate),
                          isouter=True) \
                    .filter(self.ciqpriceequity.tradingitemid.in_(ticker_group)) \
                    .filter(self.ciqpriceequity.pricingdate.between(start_datetime.date(), end_datetime.date())) \
                    .filter(or_(self.ciqexchangerate.snapid == self.exchange_rate_snap_id,
                                self.ciqexchangerate.snapid.is_(None))) \
                    .order_by(self.ciqpriceequity.pricingdate, self.ciqpriceequity.tradingitemid).statement

                # Get the string representation of timestamp field in order to use it in the read_sql function
                timestamp_string = self.ciqpriceequity.pricingdate.key
                data_frame = QFDataFrame(pd.read_sql(historical_bars, con=session.bind, index_col=timestamp_string,
                                                     parse_dates=timestamp_string)).replace([None], np.nan)
                data_frame = data_frame.rename(columns={f.value: f for f in SPField})

                def update_tickers_data_dict(_df, _tickers):
                    tickers_data_dict.update({
                        ticker: _df[_df['tradingitemid'] == sp_id][fields]
                        for ticker, sp_id in actual_tickers_to_sp_id.items() if sp_id in _tickers
                    })

                # adjust prices
                if self.use_adjusted_prices:
                    date_and_tids = self._get_corporate_actions_dates(session, ticker_group, [20, 31],
                                                                      start_datetime, end_datetime)
                    tids_with_corporate_actions = {t for _, t in date_and_tids}

                    # Adjust pricing data of tickers with corporate actions
                    if tids_with_corporate_actions:
                        div_adj_factor = self._get_div_adj_factor(session, tids_with_corporate_actions)
                        df_to_adjust = data_frame[data_frame["tradingitemid"].isin(tids_with_corporate_actions)]
                        df_to_adjust = self._get_div_adjusted_prices(df_to_adjust, date_and_tids, div_adj_factor)
                        update_tickers_data_dict(df_to_adjust, tids_with_corporate_actions)

                    # Update pricing data of the remaining tickers
                    tids_without_adjustment = set(ticker_group) - tids_with_corporate_actions
                    if tids_without_adjustment:
                        df = data_frame[data_frame["tradingitemid"].isin(tids_without_adjustment)]
                        update_tickers_data_dict(df, tids_without_adjustment)

                else:
                    update_tickers_data_dict(data_frame, ticker_group)

        data_array = tickers_dict_to_data_array(tickers_data_dict, tickers, fields)
        return normalize_data_array(data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field)

    def get_currency(self, tickers: Union[SPTicker, Sequence[SPTicker]]) -> Union[str, QFSeries]:
        """
        Function returning currency for the given selection of SPTickers.

        Parameters
        -----------
        tickers: SPTicker, Sequence[SPTicker]
            tickers of securities for which currencies should be retrieved

        Returns
        --------
        str, QFSeries
            currency for the given tickers
        """

        tickers, got_single_ticker = convert_to_list(tickers, SPTicker)
        currencies = QFSeries()
        sp_id_to_ticker = {t.tradingitem_id: t for t in tickers}

        with self._db_connection_provider.Session.begin() as session:
            for ticker_group in grouper(1000, sp_id_to_ticker.keys()):
                sql_statement = session.query(self.ciqtradingitem.tradingitemid, self.ciqcurrency.isocode) \
                    .join(self.ciqcurrency, self.ciqtradingitem.currencyid == self.ciqcurrency.currencyid) \
                    .filter(self.ciqtradingitem.tradingitemid.in_(ticker_group)).statement

                index_col = self.ciqtradingitem.tradingitemid.key
                currency = QFSeries(pd.read_sql(sql_statement, con=session.bind, index_col=index_col).iloc[:, 0])
                currency = currency.rename(index=sp_id_to_ticker)
                currencies = pd.concat([currencies, currency])

        currencies = currencies.reindex(tickers).replace({np.nan: None})
        return currencies[0] if got_single_ticker else currencies

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return {SPTicker}

    def _fields_to_adjust(self) -> Set[SPField]:
        """
        Return a list of fields available in the Data Provider which are either adjustable or can be translated into
        a different currency (USD).
        """
        return {SPField.AskPrice, SPField.BidPrice, SPField.LowPrice, SPField.HighPrice, SPField.OpenPrice,
                SPField.ClosePrice}

    def _get_futures_chain_dict(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                expiration_date_fields: Union[str, Sequence[str]]) -> Dict[FutureTicker, QFDataFrame]:
        raise NotImplementedError()

    def expiration_date_field_str_map(self, ticker: Ticker = None) -> Dict[ExpirationDateField, str]:
        raise NotImplementedError()

    def _get_div_adjusted_prices(self, data_frame, date_and_tids, div_adj_factor):
        data_frame_slice = data_frame.set_index(['tradingitemid'], append=True)

        indices_union = data_frame_slice.index.union(div_adj_factor.index)
        data_frame_slice = data_frame_slice.reindex(index=indices_union)
        div_adj_factor = div_adj_factor.reindex(index=indices_union).groupby(level=1).ffill()

        date_and_tids = div_adj_factor.index.intersection(date_and_tids)
        vals = div_adj_factor.groupby(level=1).shift(1).loc[date_and_tids] / div_adj_factor.loc[date_and_tids]
        ratio = vals.groupby(level=1).cumprod().reindex_like(div_adj_factor, method="bfill") \
            .groupby(level=1).shift(-1).fillna(1.0)

        fields = list(self._fields_to_adjust().intersection(data_frame_slice.columns))
        data_frame_slice.loc[:, fields] = data_frame_slice.loc[:, fields].mul(ratio['divadjfactor'], axis=0)
        return data_frame_slice.reset_index(level=1)

    def _get_corporate_actions_dates(self, session: Session, ticker_group, corporate_action_ids: List[int],
                                     start_date: datetime, end_date: datetime):
        """" function to retrieve all corporate actions dates from the list of SP events after start date query """
        corporate_dates_query = session.query(self.ciqdividend.exdate, self.ciqdividend.tradingitemid).filter(
            self.ciqdividend.tradingitemid.in_(ticker_group)).filter(
            self.ciqdividend.dividendtypeid.in_(corporate_action_ids)).filter(
            self.ciqdividend.exdate >= start_date.date()).filter(self.ciqdividend.exdate <= end_date.date()).order_by(
            self.ciqdividend.exdate, self.ciqdividend.tradingitemid).distinct()

        return corporate_dates_query.all()

    def _get_div_adj_factor(self, session: Session, ticker_group):
        query_adj_factor = session.query(self.ciqpriceequitydivadjfactor.fromdate,
                                         self.ciqpriceequitydivadjfactor.divadjfactor,
                                         self.ciqpriceequitydivadjfactor.tradingitemid) \
            .filter(self.ciqpriceequitydivadjfactor.tradingitemid.in_(ticker_group)) \
            .order_by(self.ciqpriceequitydivadjfactor.fromdate, self.ciqpriceequitydivadjfactor.tradingitemid).statement

        return pd.read_sql(query_adj_factor, con=session.bind, index_col=['fromdate', 'tradingitemid'])

    @property
    def _supported_tables(self) -> list[str]:
        return ['ciqcompany', 'ciqpriceequity', 'ciqsecurity', 'ciqtradingitem', 'ciqsimpleindustry',
                'ciqcurrency', 'ciqpriceequitydivadjfactor', 'ciqdividend', 'ciqexchangerate']
