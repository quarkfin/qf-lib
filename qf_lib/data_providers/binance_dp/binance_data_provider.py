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
from typing import Union, Sequence

import pytz
import pandas as pd
from binance import Client
from numpy import float64

from qf_lib.brokers.binance_broker.binance_contract_ticker_mapper import BinanceContractTickerMapper
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
import os
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.data_providers.csv.csv_data_provider import CSVDataProvider


class BinanceDataProvider(CSVDataProvider):
    """
    Binance Data Provider that downloads data in the range from start_date to end_date. Particularly, the data provider can be
    used in live trading with end_date corresponding to current time. Downloaded data is saved in .csv format and then
    loaded into CSVDataProvider

    Parameters
    -----------
    path: str
        path to directory where the files should be saved
    filename: str
        name of the file in which data should be saved e.g. Binance_data_{end_time.strftime("%Y-%m-%d %H_%M_%S")}.csv
    tickers: Union[Ticker, Sequence[Ticker]]
        one or a list of tickers, used further to download the prices data
    start_date: datetime
        beginning of the data in local time (it is automatically converted to UTC time used by binance)
    end_date: datetime
        end of the data in local time (it is automatically converted to UTC time used by binance)
    frequency: Frequency = Frequency.MIN_1
        frequency of the data
    """

    def __init__(self, path: str, filename: str, tickers: Union[Ticker, Sequence[Ticker]], start_date: datetime, end_date: datetime,
                 contract_ticker_mapper: BinanceContractTickerMapper, frequency: Frequency = Frequency.MIN_1):

        if frequency not in [Frequency.DAILY, Frequency.MIN_1]:
            raise NotImplementedError("Only 1m and DAILY freq is supported now")

        self.contract_ticker_mapper = contract_ticker_mapper

        tickers, _ = convert_to_list(tickers, Ticker)

        self.frequency_mapping = {
            Frequency.DAILY: '1d',
            Frequency.MIN_1: '1m'
        }

        index_col = 'Dates'
        field_to_price_field_dict = {'Open': PriceField.Open, 'High': PriceField.High, 'Low': PriceField.Low,
                                     'Close': PriceField.Close, 'Volume': PriceField.Volume}
        fields = ['Open', 'High', 'Low', 'Close', 'Volume']
        ticker_col = 'Ticker'

        self.logger = qf_logger.getChild(self.__class__.__name__)

        self.logger.info("creating BinanceDataProvider")
        self.client = Client()

        filepath = os.path.join(path, filename)

        self._load_data(filepath, tickers, fields, start_date, end_date, frequency, index_col, ticker_col)

        super().__init__(filepath, tickers, index_col, field_to_price_field_dict, fields, start_date, end_date, frequency, ticker_col=ticker_col)

    def _load_data(self, filepath, tickers, fields, start_date, end_date, frequency, index_col, ticker_col):
        if not os.path.isfile(filepath):
            list_of_dfs = [self._download_binance_data_df(ticker, start_date, end_date, frequency, ticker_col) for ticker in tickers]
        else:

            list_of_dfs = []
            df = pd.read_csv(filepath, index_col=index_col, parse_dates=['Dates'], engine='python')

            infer_freq = Frequency.infer_freq(df.index)

            if infer_freq != frequency:
                raise ValueError(f'Requested frequency: {frequency} is different from the one in the file: {infer_freq}')

            for ticker in tickers:

                current_df = df[df[ticker_col] == ticker.as_string()]

                if current_df.empty:
                    current_end_date = start_date
                else:
                    current_end_date = current_df.index[-1].to_pydatetime()

                    if current_end_date == end_date:
                        list_of_dfs.append(current_df)
                        continue

                df_to_append = self._download_binance_data_df(ticker, current_end_date, end_date, frequency, ticker_col)
                combined_df = pd.concat([current_df, df_to_append])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]  # to have the most recent bar data updated
                list_of_dfs.append(combined_df)

        df = pd.concat(list_of_dfs)
        df.loc[:, fields] = df.loc[:, fields].astype(float64)
        df.to_csv(filepath)

    def _download_binance_data_df(self, ticker, start_time: datetime, end_time: datetime, frequency, ticker_col) -> QFDataFrame:
        start_time = start_time + RelativeDelta(second=0, microsecond=0)
        end_time = end_time + RelativeDelta(second=0, microsecond=0)

        # the requested time has to be in UTC
        start_time_str = start_time.astimezone(pytz.UTC).strftime(DateFormat.FULL_ISO.format_string)
        end_time_str = end_time.astimezone(pytz.UTC).strftime(DateFormat.FULL_ISO.format_string)

        res_dict = {'Dates': [], 'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': [], ticker_col: []}

        symbol = self.contract_ticker_mapper.ticker_to_contract(ticker)

        res = self.client.get_historical_klines(symbol=symbol,
                                                interval=self.frequency_mapping[frequency],
                                                start_str=start_time_str, end_str=end_time_str, limit=1000)

        for i in res:
            # response is parsed to local time from unix milliseconds
            res_dict['Dates'].append(datetime.fromtimestamp(i[0] / 1000).strftime('%Y-%m-%d %H:%M:%S'))
            res_dict['Open'].append(i[1])
            res_dict['High'].append(i[2])
            res_dict['Low'].append(i[3])
            res_dict['Close'].append(i[4])
            res_dict['Volume'].append(i[5])
            res_dict[ticker_col].append(ticker.as_string())

        df = QFDataFrame(res_dict).set_index('Dates')
        df.index = pd.to_datetime(df.index, format=str(DateFormat.FULL_ISO))

        missing_dates = pd.date_range(start=start_time, end=end_time, freq=frequency.to_pandas_freq()).difference(df.index)

        if not missing_dates.empty:
            self.logger.info(f'Missing dates: {missing_dates} for ticker: {ticker}')

        df = df[~df.index.duplicated(keep='first')]
        return df
