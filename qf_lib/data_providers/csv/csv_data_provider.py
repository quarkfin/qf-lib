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
from pathlib import Path
from typing import Sequence, Union, List, Dict, Optional

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.helpers import normalize_data_array, tickers_dict_to_data_array
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class CSVDataProvider(PresetDataProvider):
    """
    Generic Data Provider that loads csv files. All the files should have a certain naming convention (see Notes).
    Additionally, the data provider requires providing mapping between header names in the file and corresponding
    price fields in the form of dictionary where the key is a column name in the csv file, and the value is
    a corresponding PriceField. Please note that this is required to use get_price method

    Parameters
    -----------
    path: str
        it should be either path to the directory containing the CSV files or path to the specific file when ticker_col
        is used and only one file should be loaded
    tickers: Ticker, Sequence[Ticker]
        one or a list of tickers, used further to download the prices data
    index_col: str
        Label of the dates / timestamps column, which will be later on used to index the data.
        No need to repeat it in the fields.
    field_to_price_field_dict: Optional[Dict[str, PriceField]]
        mapping of header names to PriceField. It is required to call get_price method which uses PriceField enum.
        In the mapping, the key is a column name, and the value is a corresponding PriceField.
        for example if header for open price is called 'Open price' put mapping  {'Open price': Pricefield:Open}
        Preferably map all: open, high, low, close to corresponding price fields.
    fields: Optional[str, List[str]]
        all columns that will be loaded to the CSVDataProvider from given file.
        these fields will be available in get_history method.
        By default all fields (columns) are loaded.
    start_date: Optional[datetime]
        first date to be downloaded
    end_date: Optional[datetime]
        last date to be downloaded
    frequency: Optional[Frequency]
        frequency of the data. The parameter is optional, and by default equals to daily Frequency.
    dateformat: Optional[str]
        the strftime to parse time, e.g. "%d/%m/%Y". Parameter is Optional and if not provided, the data provider will
        try to infer the dates format from the data. By default None.
    ticker_col: Optional[str]
        column name with the tickers

    Notes
    -----
        - FutureTickers are not supported by this data provider.
        - By default, data for each ticker should be in a separate file named after this tickers' string representation
        (in most cases it is simply its name, to check what is the string representation of a given ticker use
        Ticker.as_string() function). However, you can also load one file containing all data with specified tickers in
        one column row by row as it is specified in demo example file daily_data.csv or intraday_data.csv.
        In order to do so you need to specify the name of the ticker column in ticker_col and specify the path to the
        file.
        - Please note that when using ticker_col it is required to provide the path to specific file (loading is not
        based on ticker names as it is in the default approach)
        - By providing mapping field_to_price_field_dict you are able to use get_price method which allows you to
        aggregate intraday data (currently, get_history does not allow using intraday data aggregation)

    Example
    -----
        start_date = str_to_date("2018-01-01")
        end_date = str_to_date("2022-01-01")

        index_column = 'Open time'
        field_to_price_field_dict = {
            'Open': PriceField.Open,
            'High': PriceField.High,
            'Low': PriceField.Low,
            'Close': PriceField.Close,
            'Volume': PriceField.Volume,
        }

        tickers = #create your ticker here. ticker.as_string() should match file name, unless you specify ticker_col
        path = "C:\\data_dir"
        data_provider = CSVDataProvider(path, tickers, index_column, field_to_price_field_dict, start_date,
                                        end_date, Frequency.MIN_1)
    """
    def __init__(self, path: str, tickers: Union[Ticker, Sequence[Ticker]], index_col: str,
                 field_to_price_field_dict: Optional[Dict[str, PriceField]] = None,
                 fields: Optional[Union[str, List[str]]] = None, start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None, frequency: Optional[Frequency] = Frequency.DAILY,
                 dateformat: Optional[str] = None, ticker_col: Optional[str] = None):

        self.logger = qf_logger.getChild(self.__class__.__name__)

        if fields:
            fields, _ = convert_to_list(fields, str)

        # Convert to list and remove duplicates
        tickers, _ = convert_to_list(tickers, Ticker)
        tickers = list(dict.fromkeys(tickers))
        assert len([t for t in tickers if isinstance(t, FutureTicker)]) == 0, "FutureTickers are not supported by " \
                                                                              "this data provider"

        data_array, start_date, end_date, available_fields = self._get_data(path, tickers, fields, start_date, end_date,
                                                                            frequency, field_to_price_field_dict,
                                                                            index_col, dateformat, ticker_col)

        normalized_data_array = normalize_data_array(data_array, tickers, available_fields, False, False, False)

        super().__init__(data=normalized_data_array,
                         start_date=start_date,
                         end_date=end_date,
                         frequency=frequency)

    def _get_data(self, path: str, tickers: Sequence[Ticker], fields: Optional[Sequence[str]], start_date: datetime,
                  end_date: datetime, frequency: Frequency, field_to_price_field_dict: Optional[Dict[str, PriceField]],
                  index_col: str, dateformat: str, ticker_col):

        tickers_str_mapping = {ticker.as_string(): ticker for ticker in tickers}
        tickers_prices_dict = {}
        available_fields = set()

        def _process_df(df, ticker_str):
            df.index = pd.to_datetime(df[index_col], format=dateformat)
            df = df[~df.index.duplicated(keep='first')]
            df = df.drop(index_col, axis=1)
            if Frequency.infer_freq(df.index) != frequency:
                self.logger.info(f"Inferred frequency for the file {path} is different than requested. "
                                 f"Skipping {path}.")
            else:

                start_time = start_date or df.index[0]
                end_time = end_date or df.index[-1]

                if fields:
                    df = df.loc[start_time:end_time, df.columns.isin(fields)]
                    fields_diff = set(fields).difference(df.columns)
                    if fields_diff:
                        self.logger.info(f"Not all fields are available for {path}. Difference: {fields_diff}")
                else:
                    df = df.loc[start_time:end_time, :]
                    available_fields.update(df.columns.tolist())

                if field_to_price_field_dict:
                    for key, value in field_to_price_field_dict.items():
                        df[value] = df[key]

                if ticker_str in tickers_str_mapping:
                    tickers_prices_dict[tickers_str_mapping[ticker_str]] = df
                else:
                    self.logger.info(f'Ticker {ticker_str} was not requested in the list of tickers. Skipping.')

        if ticker_col:
            df = QFDataFrame(pd.read_csv(path, dtype={index_col: str}))
            available_tickers = df[ticker_col].dropna().unique().tolist()

            for ticker_str in available_tickers:
                sliced_df = df[df[ticker_col] == ticker_str]
                _process_df(sliced_df, ticker_str)

        else:
            tickers_paths = [list(Path(path).glob('**/{}.csv'.format(ticker.as_string()))) for ticker in tickers]
            joined_tickers_paths = [item for sublist in tickers_paths for item in sublist]

            for path in joined_tickers_paths:
                ticker_str = path.resolve().name.replace('.csv', '')
                df = QFDataFrame(pd.read_csv(path, dtype={index_col: str}))
                _process_df(df, ticker_str)

        if not tickers_prices_dict.values():
            raise ImportError("No data was found. Check the correctness of all data")

        if fields:
            available_fields = list(fields)
        else:
            available_fields = list(available_fields)

        if field_to_price_field_dict:
            available_fields.extend(list(field_to_price_field_dict.values()))

        if not start_date:
            start_date = min(list(df.index.min() for df in tickers_prices_dict.values()))

        if not end_date:
            end_date = max(list(df.index.max() for df in tickers_prices_dict.values()))

        result = tickers_dict_to_data_array(tickers_prices_dict, list(tickers_prices_dict.keys()), available_fields), \
            start_date, end_date, available_fields
        return result
