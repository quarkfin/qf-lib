from datetime import datetime
from datetime import datetime
from itertools import groupby
from typing import Union, Sequence, Dict

import pandas as pd
import quandl

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.helpers import tickers_dict_to_data_array, \
    normalize_data_array, get_fields_from_tickers_to_data_dict
from qf_lib.settings import Settings


class QuandlDataProvider(AbstractPriceDataProvider):
    """"
    The table database: WIKI/PRICES offers stock prices, dividends and splits for 3000 US publicly-traded companies.
    This database is updated at 9:15 PM EST every weekday.
    """

    def __init__(self, settings: Settings):
        self.key = settings.quandl_key
        quandl.ApiConfig.api_key = self.key
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_history(self, tickers: Union[QuandlTicker, Sequence[QuandlTicker]],
                    fields: Union[None, str, Sequence[str]]=None,
                    start_date: datetime=None, end_date: datetime=None, **kwargs) \
            -> Union[QFSeries, QFDataFrame, pd.Panel]:
        """
        NOTE: Only use one Quandl Database at the time.
        Do not mix multiple databases in one query - this is the natural limitation coming from the fact that column
        names (fields) are different across databases.
        """
        tickers, got_single_ticker = convert_to_list(tickers, QuandlTicker)
        got_single_date = self._is_single_date(start_date, end_date)

        if fields is not None:
            fields, got_single_field = convert_to_list(fields, (PriceField, str))
        else:
            got_single_field = False  # all existing fields will be present in the result

        db_type = tickers[0].database_type
        if db_type == QuandlDBType.Table:
            result_dict = self._get_history_from_table(tickers, fields, start_date, end_date)
        elif db_type == QuandlDBType.Timeseries:
            result_dict = self._get_history_from_timeseries(tickers, fields, start_date, end_date)
        else:
            raise LookupError("Quandl Database type: {} is not supported.".format(db_type))

        if fields is None:
            fields = get_fields_from_tickers_to_data_dict(result_dict)

        result_data_array = tickers_dict_to_data_array(result_dict, tickers, fields)

        normalized_result = normalize_data_array(
            result_data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field
        )

        return normalized_result

    def _get_fields_from_result(self, result_dict):
        fields = set()
        for dates_fields_values in result_dict.values():
            fields.update(dates_fields_values.fields.values)

        fields = list(fields)
        return fields

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
                                start_date: datetime, end_date: datetime) -> Dict[QuandlTicker, pd.DataFrame]:
        # Possibly this method is not generic enough, but I couldn't find another table db to test it.

        field_options = {}
        if fields is not None:
            columns = ['ticker', 'date'] + list(fields)
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
                dates_fields_values_df = self._format_single_ticker_table(ticker_df, start_date, end_date)
                result_dict[ticker] = dates_fields_values_df

        return result_dict

    def _get_history_from_timeseries(self, tickers: Sequence[QuandlTicker], fields: Sequence[str],
                                     start_date: datetime, end_date: datetime):
        """
        NOTE: Only use one Quandl Database at the time. Do not mix multiple databases.
        """
        databases = {ticker.database_name for ticker in tickers}
        if len(databases) > 1:
            raise ValueError("Mixed databases in one request are not supported yet")

        tickers = list(tickers)  # allows iterating the sequence more then once
        tickers_str = [t.as_string() for t in tickers]

        kwargs = {}
        if start_date is not None:
            kwargs['start_date'] = date_to_str(start_date)
        if end_date is not None:
            kwargs['end_date'] = date_to_str(end_date)

        data = quandl.get(tickers_str, **kwargs)  # type: pd.DataFrame

        def extract_ticker_name(column_name):
            ticker_str, _ = column_name.split(' - ')
            ticker = QuandlTicker.from_string(ticker_str)
            return ticker

        ticker_grouping = data.groupby(extract_ticker_name, axis=1)
        ticker_to_df = {}  # type: Dict[str, pd.DataFrame]  # string -> DataFrame[dates, fields]
        for ticker, ticker_data_df in ticker_grouping:
            tickers_and_fields = (column_name.split(' - ') for column_name in ticker_data_df.columns)
            field_names = [field for (ticker, field) in tickers_and_fields]
            ticker_data_df.columns = field_names

            if fields is not None:
                # select only required fields
                ticker_data_df = self._select_only_required_fields(ticker, ticker_data_df, fields)

                # if there was no data for the given ticker, skip the ticker
                if ticker_data_df is None:
                    continue

            ticker_to_df[ticker] = ticker_data_df

        return ticker_to_df

    def _select_only_required_fields(self, ticker, ticker_data, fields):
        requested_fields_set = set(fields)
        got_fields_set = set(ticker_data.columns)
        missing_fields = requested_fields_set - got_fields_set

        if missing_fields:
            missing_columns = [ticker.field_to_column_name(field) for field in missing_fields]
            self.logger.warning(
                "Columns {} have not been found in the Quandl response".format(missing_columns))

        fields_to_select = requested_fields_set.intersection(got_fields_set)

        # if there are no fields which should be selected, return None
        if not fields_to_select:
            result = None
        else:
            result = ticker_data.loc[:, fields_to_select]

        return result

    @staticmethod
    def _format_single_ticker_table(table: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # create index from column and remove redundant info
        table.set_index(keys='date', inplace=True)
        table = table.drop('ticker', axis=1)

        # cut the dates if necessary
        table = table.loc[start_date:end_date]

        return table
