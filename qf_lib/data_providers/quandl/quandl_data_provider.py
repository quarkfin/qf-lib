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
import warnings
from datetime import datetime
from itertools import groupby
from typing import Union, Sequence, Dict

import pandas as pd
from qf_lib.common.enums.expiration_date_field import ExpirationDateField

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.quandl_db_type import QuandlDBType
from qf_lib.common.tickers.tickers import QuandlTicker, Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import tickers_dict_to_data_array, \
    normalize_data_array, get_fields_from_tickers_data_dict
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.settings import Settings

try:
    import quandl
    is_quandl_installed = True
except ImportError:
    is_quandl_installed = False
    warnings.warn("No quandl installed. If you would like to use QuandlDataProvider first install the quandl library.")


class QuandlDataProvider(DataProvider):
    """
    Class providing the Quandl data.
    The table database: WIKI/PRICES offers stock prices, dividends and splits for 3000 US publicly-traded companies.
    This database is updated at 9:15 PM EST every weekday.
    """

    def __init__(self, settings: Settings):
        super().__init__()
        self.logger = qf_logger.getChild(self.__class__.__name__)

        try:
            self.key = settings.quandl_key
            quandl.ApiConfig.api_key = self.key
        except AttributeError:
            self.logger.warning("No quandl_key parameter found in Settings. If you want to use QuandlDataProvider, add "
                                "quandl_key in the settings json file.")

    def get_price(self, tickers: Union[QuandlTicker, Sequence[QuandlTicker]],
                  fields: Union[PriceField, Sequence[PriceField]], start_date: datetime, end_date: datetime = None,
                  frequency: Frequency = Frequency.DAILY):
        start_date = self._adjust_start_date(start_date, frequency)
        return self._get_history(
            convert_to_prices_types=True, tickers=tickers, fields=fields, start_date=start_date, end_date=end_date)

    def get_history(
            self, tickers: Union[QuandlTicker, Sequence[QuandlTicker]], fields: Union[None, str, Sequence[str]] = None,
            start_date: datetime = None, end_date: datetime = None, **kwargs):
        return self._get_history(
            convert_to_prices_types=False, tickers=tickers, fields=fields, start_date=start_date, end_date=end_date)

    def _get_history(
            self, convert_to_prices_types: bool, tickers: Union[QuandlTicker, Sequence[QuandlTicker]],
            fields: Union[None, str, Sequence[str], PriceField, Sequence[PriceField]] = None,
            start_date: datetime = None, end_date: datetime = None) -> \
            Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        NOTE: Only use one Quandl Database at the time.
        Do not mix multiple databases in one query - this is the natural limitation coming from the fact that column
        names (fields) are different across databases.
        """
        tickers, got_single_ticker = convert_to_list(tickers, QuandlTicker)
        got_single_date = start_date is not None and (start_date == end_date)

        if fields is not None:
            fields, got_single_field = convert_to_list(fields, (PriceField, str))
        else:
            got_single_field = False  # all existing fields will be present in the result

        result_dict = {}
        for db_name, ticker_group in groupby(tickers, lambda t: t.database_name):
            ticker_group = list(ticker_group)

            partial_result_dict = self._get_result_for_single_database(
                convert_to_prices_types, ticker_group, fields, start_date, end_date)

            result_dict.update(partial_result_dict)

        if fields is None:
            fields = get_fields_from_tickers_data_dict(result_dict)

        result_data_array = tickers_dict_to_data_array(result_dict, tickers, fields)

        normalized_result = normalize_data_array(
            result_data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field,
            use_prices_types=convert_to_prices_types)

        return normalized_result

    def _get_result_for_single_database(self, convert_to_prices_types, ticker_group, fields, start_date, end_date):
        first_ticker = ticker_group[0]  # type: QuandlTicker
        db_name = first_ticker.database_name
        db_type = first_ticker.database_type

        if convert_to_prices_types:
            fields_as_strings = self._map_fields_to_str(fields, db_name, db_type)
        else:
            fields_as_strings = fields

        if db_type == QuandlDBType.Table:
            partial_result_dict = self._get_history_from_table(
                ticker_group, fields_as_strings, start_date, end_date)
        elif db_type == QuandlDBType.Timeseries:
            partial_result_dict = self._get_history_from_timeseries(
                ticker_group, fields_as_strings, start_date, end_date)
        else:
            raise LookupError("Quandl Database type: {} is not supported.".format(db_type))

        if convert_to_prices_types:
            str_to_field = self._str_to_price_field_map(db_name, db_type)
            for ticker_data_df in partial_result_dict.values():
                price_field_columns = [str_to_field[field_str] for field_str in ticker_data_df.columns]
                ticker_data_df.columns = price_field_columns

        return partial_result_dict

    def _get_fields_from_result(self, result_dict):
        fields = set()
        for dates_fields_values in result_dict.values():
            fields.update(dates_fields_values.fields.values)

        fields = list(fields)
        return fields

    def supported_ticker_types(self):
        return {QuandlTicker}

    def _map_fields_to_str(self, fields: Sequence[PriceField], database_name: str, database_type: QuandlDBType):
        field_to_str = self._price_field_to_str_map(database_name, database_type)
        fields_as_strings = [field_to_str[field] for field in fields]
        return fields_as_strings

    def _str_to_price_field_map(self, database_name: str, database_type: QuandlDBType):
        field_to_str = self._price_field_to_str_map(database_name, database_type)
        str_to_field = {field_str: field for field, field_str in field_to_str.items()}

        return str_to_field

    def _price_field_to_str_map(self, database_name: str, database_type: QuandlDBType) -> Dict[PriceField, str]:
        if database_type == QuandlDBType.Table and database_name == 'WIKI/PRICES':
            price_field_dict = {
                PriceField.Open: 'adj_open',
                PriceField.High: 'adj_high',
                PriceField.Low: 'adj_low',
                PriceField.Close: 'adj_close',
                PriceField.Volume: 'adj_volume'
            }
        elif database_name == 'WIKI':
            price_field_dict = {
                PriceField.Open: 'Adj. Open',
                PriceField.High: 'Adj. High',
                PriceField.Low: 'Adj. Low',
                PriceField.Close: 'Adj. Close',
                PriceField.Volume: 'Adj. Volume'
            }
        elif database_name == 'WSE':
            price_field_dict = {
                PriceField.Open: 'Open',
                PriceField.High: 'High',
                PriceField.Low: 'Low',
                PriceField.Close: 'Close',
                PriceField.Volume: 'Volume'
            }
        elif database_name == 'CHRIS':
            # database of continuous futures - only Previous Settlement available
            price_field_dict = {
                PriceField.Close: 'Previous Settlement',
            }
        elif database_name in ['ICE', 'CME', 'EUREX']:
            # mapping for individual futures contracts
            price_field_dict = {
                PriceField.Open: 'Open',
                PriceField.High: 'High',
                PriceField.Low: 'Low',
                PriceField.Close: 'Settle',
                PriceField.Volume: 'Volume'
            }
        else:
            raise LookupError(
                "Quandl Database: {} is not supported. PriceField -> string mapping is required.".format(database_name)
            )
        return price_field_dict

    def _get_history_from_table(self, tickers_of_single_db: Sequence[QuandlTicker], fields: Sequence[str],
                                start_date: datetime, end_date: datetime) -> Dict[QuandlTicker, pd.DataFrame]:
        # Possibly this method is not generic enough, but I couldn't find another table db to test it.
        field_options = {}
        if fields is not None:
            columns = ['ticker', 'date'] + list(fields)
            field_options['qopts'] = {'columns': columns}

        db_name = tickers_of_single_db[0].database_name
        result_dict = {}

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

    def _get_history_from_timeseries(
            self, tickers: Sequence[QuandlTicker], fields: Sequence[str], start_date: datetime, end_date: datetime):
        """
        NOTE: Only use one Quandl Database at the time. Do not mix multiple databases.
        """
        tickers = list(tickers)  # allows iterating the sequence more then once
        tickers_map = {t.as_string(): t for t in tickers}

        kwargs = {}
        if start_date is not None:
            kwargs['start_date'] = date_to_str(start_date)
        if end_date is not None:
            kwargs['end_date'] = date_to_str(end_date)

        data = quandl.get(list(tickers_map.keys()), **kwargs)  # type: pd.DataFrame

        def extract_ticker_name(column_name):
            ticker_str, _ = column_name.split(' - ')
            ticker = tickers_map[ticker_str]
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
            self.logger.warning("Columns {} have not been found in the Quandl response".format(missing_columns))

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
        table = table.drop('ticker', axis=1)  # type: pd.DataFrame
        table = table.sort_index()

        # cut the dates if necessary
        table = table.loc[start_date:end_date]

        return table

    def get_futures_chain_tickers(self, tickers: Union[FutureTicker, Sequence[FutureTicker]],
                                  expiration_date_fields: Union[ExpirationDateField, Sequence[ExpirationDateField]]) \
            -> Dict[FutureTicker, Union[QFSeries, QFDataFrame]]:
        raise NotImplementedError("Downloading Future Chain Tickers in QuandlDataProvider is not supported yet")

    def expiration_date_field_str_map(self, ticker: Ticker = None) -> Dict[ExpirationDateField, str]:
        pass
