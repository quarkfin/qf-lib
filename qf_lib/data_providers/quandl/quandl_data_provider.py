import logging
from datetime import datetime
from itertools import groupby
from typing import Union, Sequence, Dict

import pandas as pd
import quandl

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.settings import Settings


class QuandlDataProvider(AbstractPriceDataProvider):
    """"
    The table database: WIKI/PRICES offers stock prices, dividends and splits for 3000 US publicly-traded companies.
    This database is updated at 9:15 PM EST every weekday.
    """

    def __init__(self, settings: Settings):
        self.key = settings.quandl_key
        quandl.ApiConfig.api_key = self.key
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_history(self, tickers: Union[QuandlTicker, Sequence[QuandlTicker]],
                    fields: Union[None, str, Sequence[str]]=None,
                    start_date: datetime=None, end_date: datetime=None, **kwargs) \
            -> Union[QFSeries, QFDataFrame, pd.Panel]:
        """
        When fields is None, all available fields will be returned
        NOTE: Only use one Quandl Database at the time.
        Do not mix multiple databases in one query - this is the natural limitation coming from the fact that column
        names (fields) are different across databases.
        """
        tickers, got_single_ticker = convert_to_list(tickers, QuandlTicker)

        if fields is not None:
            fields, got_single_field = convert_to_list(fields, (PriceField, str))
        else:
            got_single_field = False

        db_type = tickers[0].database_type
        if db_type == QuandlDBType.Table:
            result_dict = self._get_history_from_table(tickers, fields, start_date, end_date)
        elif db_type == QuandlDBType.Timeseries:
            result_dict = self._get_history_from_timeseries(tickers, fields, start_date, end_date)
        else:
            raise LookupError("Quandl Database type: {} is not supported.".format(db_type))

        panel = self._dict_to_panel_or_df(result_dict, tickers, fields)
        got_single_date = self._is_single_date(start_date, end_date)
        result = self._squeeze_panel(panel, got_single_date, got_single_ticker, got_single_field)
        result = self._cast_result_to_proper_type(result)
        return result

    def supported_ticker_types(self):
        return {QuandlTicker}

    def price_field_to_str_map(self, ticker: QuandlTicker=None) -> Dict[PriceField, str]:
        if ticker.database_type == QuandlDBType.Table and ticker.database_name == 'WIKI/PRICES':
            price_field_dict = {
                PriceField.Open: 'adj_open',
                PriceField.High: 'adj_high',
                PriceField.Low: 'adj_low',
                PriceField.Close: 'adj_close',
                PriceField.Volume: 'adj_volume'
            }
        elif ticker.database_name == 'WIKI':
            price_field_dict = {
                PriceField.Open: 'Adj. Open',
                PriceField.High: 'Adj. High',
                PriceField.Low: 'Adj. Low',
                PriceField.Close: 'Adj. Close',
                PriceField.Volume: 'Adj. Volume'
            }
        elif ticker.database_name == 'WSE':
            price_field_dict = {
                PriceField.Open: 'Open',
                PriceField.High: 'High',
                PriceField.Low: 'Low',
                PriceField.Close: 'Close',
                PriceField.Volume: 'Volume'
            }
        elif ticker.database_name == 'CHRIS':
            # database of continuous futures - only Previous Settlement available
            price_field_dict = {
                PriceField.Close: 'Previous Settlement',
            }
        elif ticker.database_name == 'ICE' or ticker.database_name == 'CME' or ticker.database_name == 'EUREX':
            # mapping for individual futures contracts
            price_field_dict = {
                PriceField.Open: 'Open',
                PriceField.High: 'High',
                PriceField.Low: 'Low',
                PriceField.Close: 'Settle',
                PriceField.Volume: 'Volume'
            }
        else:
            raise LookupError("Quandl Database: {} is not supported. PriceField -> string mapping is required.".format(
                ticker.database_name))
        return price_field_dict

    def _get_history_from_table(self,  tickers: Sequence[QuandlTicker], fields: Sequence[str],
                                start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """
        Returns dict: ticker_string -> DataFrame
        """
        # Possibly this method is not generic enough, but I couldn't find another table db to test it.

        field_options = {}
        if fields is not None:
            columns = ['ticker', 'date'] + fields
            field_options['qopts'] = {'columns': columns}

        result_dict = {}
        tickers = sorted(tickers, key=lambda t: t.database_name)

        # group tickers by database and run a request for each database separately
        for db_name, tickers_of_single_db in groupby(tickers, lambda t: t.database_name):
            tickers_str = [t.as_string() for t in tickers_of_single_db]
            df = quandl.get_table(db_name, ticker=tickers_str, paginate=True, **field_options)
            # at this point we have a large DataFrame with rows corresponding to different tickers
            # we group it by ticker
            ticker_grouping = df.groupby('ticker')
            for ticker_str, ticker_df in ticker_grouping:
                ticker = QuandlTicker(ticker=ticker_str, database_name=db_name, database_type=QuandlDBType.Table)
                result_dict[ticker] = self._format_single_ticker_table(ticker_df, start_date, end_date)
        return result_dict

    def _get_history_from_timeseries(self, tickers: Sequence[QuandlTicker], fields: Sequence[str],
                                     start_date: datetime, end_date: datetime):
        """
        NOTE: Only use one Quandl Database at the time. Do not mix multiple databases.
        """

        tickers = list(tickers)  # allows iterating the sequence more then once
        tickers_str = [t.as_string() for t in tickers]

        kwargs = {}
        if start_date is not None:
            kwargs['start_date'] = date_to_str(start_date)
        if end_date is not None:
            kwargs['end_date'] = date_to_str(end_date)

        data = quandl.get(tickers_str, **kwargs)

        result_dict = {}
        if fields is not None:
            # we only pick provided fields to dict: ticker_str -> DataFrame
            for ticker in tickers:
                ticker_df = QFDataFrame()
                for field in fields:
                    column_name = ticker.field_to_column_name(field)
                    if column_name in data.columns:
                        ticker_df[field] = data[column_name]
                    else:
                        self.logger.warning("Column '{}' has not been found in the Quandl response".format(column_name))

                result_dict[ticker] = ticker_df
        else:
            # we map all column names to dict: ticker_str -> DataFrame
            for column_name in data.columns:
                ticker_str, field_str = column_name.split(' - ')
                ticker = QuandlTicker.from_string(ticker_str)
                if ticker in result_dict:
                    # add column to the existing data frame
                    df = result_dict[ticker]
                    df[field_str] = data[column_name]
                else:
                    # add new data frame to the result dict
                    df = QFDataFrame()
                    df[field_str] = data[column_name]
                    result_dict[ticker] = df

        return result_dict

    @staticmethod
    def _format_single_ticker_table(table: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # create index from column and remove redundant info
        table.set_index(keys='date', inplace=True)
        table = table.drop('ticker', axis=1)

        # cut the dates if necessary
        table = table.loc[start_date:end_date]

        return table

    @staticmethod
    def _dict_to_panel_or_df(tickers_to_data_dict: dict, tickers: Sequence[QuandlTicker], fields) -> pd.Panel:
        """
        Converts a dictionary tickers->DateFrame to Panel.

        Parameters
        ----------
        tickers_to_data_dict: dict[str, pd.DataFrame]

        Returns
        -------
        pandas.Panel  [date, ticker, field] or
        QFDataFrame [date, tickers] if single field was provided

        """
        panel = pd.Panel.from_dict(data=tickers_to_data_dict)

        # recombines dimensions, so that the first one is date, major is ticker, minor is field
        panel = panel.transpose(1, 0, 2)

        # to keep the order of tickers and fields we reindex the panel
        if fields is not None:
            fields = pd.np.array(fields, ndmin=1)  # to handle single and many fields.
            panel = panel.reindex(major_axis=tickers, minor_axis=fields)
        else:
            panel = panel.reindex(major_axis=tickers)

        return panel
