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
from typing import Sequence, Union, List
from pathlib import Path

import pandas as pd

from qf_lib.common.enums.expiration_date_field import ExpirationDateField
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker, PortaraTicker
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import tickers_dict_to_data_array, chain_tickers_within_range, normalize_data_array
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class PortaraDataProvider(PresetDataProvider):
    """
    Loads Portara data for futures contracts. When it comes to futures, this provider supports both continuous series
    and working on individual contracts (tenors).

    The required format is .csv for pricing data (with headers) and .txt for expiration dates data.

    Parameters
    -----------
    path: str
        path to the exported Portara data
    tickers: Ticker, Sequence[Ticker]
        one or a list of tickers, used further to download the futures contracts related data.
        The list can contain either Tickers or FutureTickers. In case of the Tickers, simply the given fields
        are being downloaded and stored using the PresetDataProvider. In case of the FutureTickers, the future
        chain tickers and their corresponding prices are being downloaded and stored.
    fields: PriceField, Sequence[PriceField]
        fields that should be downloaded
    start_date: datetime
        first date to be downloaded
    end_date: datetime
        last date to be downloaded
    frequency: Frequency
        frequency of the data (1-minute bar and daily frequencies are supported)

    Notes
    -----

        - It is assumed that the names of files containing prices data match the names of the contracts (e.g.
          SI1999Z.csv for SI1999Z).
        - The naming convention used to generate the data in Portara should be the "SymYYYYM".
        - The date format should be set to "YYYY-MM-DD".
        - Currently the only supported data frequencies are daily frequency and 1-minute bar frequency. After preloading
          1-minute bars, it is possible to aggregate them selecting a different frequency in the get price.
        - In order to see exemplary files which may be used with the PortaraDataProvider (e.g. structure of expiration
          dates file), check the mock files in the tests directory:
          tests > unit_tests > data_providers > portara > input_data.
        - To see examples using Portara data provider, check the demo scripts:
          demo_scripts > data_providers > portara.

    """

    def __init__(self, path: str, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, List[PriceField]],
                 start_date: datetime, end_date: datetime, frequency: Frequency):

        self.logger = qf_logger.getChild(self.__class__.__name__)

        if frequency not in [Frequency.DAILY, Frequency.MIN_1]:
            raise NotImplementedError("{} supports only DAILY and MIN_1 bars loading".format(self.__class__.__name__))

        fields, _ = convert_to_list(fields, PriceField)

        # Convert to list and remove duplicates
        tickers, _ = convert_to_list(tickers, Ticker)
        tickers = list(dict.fromkeys(tickers))

        future_tickers = [ticker for ticker in tickers if isinstance(ticker, FutureTicker)]
        non_future_tickers = [ticker for ticker in tickers if not isinstance(ticker, FutureTicker)]

        exp_dates = None
        all_tickers = non_future_tickers

        if future_tickers:
            exp_dates = self._get_expiration_dates(path, future_tickers)

            # Filter out all theses specific future contracts, which expired before start_date
            for ft in future_tickers:
                all_tickers.extend(chain_tickers_within_range(ft, exp_dates[ft], start_date, end_date))

        data_array, contracts_df = self._get_price_and_contracts(path, all_tickers, fields, start_date,
                                                                 end_date, frequency)
        normalized_data_array = normalize_data_array(data_array, all_tickers, fields, False, False, False)

        self._contracts_df = contracts_df

        super().__init__(data=normalized_data_array,
                         exp_dates=exp_dates,
                         start_date=start_date,
                         end_date=end_date,
                         frequency=frequency)

    def get_contracts_df(self) -> QFDataFrame:
        """ Returns contracts information. A non empty data frame is returned only if the pricing data files contain
        the 'Contract' column. """
        return self._contracts_df

    def _get_expiration_dates(self, dir_path: str, future_tickers: Sequence[FutureTicker]):
        tickers_dates_dict = {}

        for future_ticker in future_tickers:
            for path in list(Path(dir_path).glob('**/{}.txt'.format(future_ticker.family_id.replace("{}", "")))):
                try:
                    path = path.resolve()
                    df = pd.read_csv(path, names=['Contract', 'Expiration Date'], parse_dates=['Expiration Date'],
                                     date_parser=lambda date: datetime.strptime(date, '%Y%m%d'), index_col="Contract")
                    df = df.rename(columns={'Expiration Date': ExpirationDateField.LastTradeableDate})
                    df.index = PortaraTicker.from_string(df.index, security_type=future_ticker.security_type,
                                                         point_value=future_ticker.point_value)

                    if all(future_ticker.belongs_to_family(x) for x in df.index):
                        tickers_dates_dict[future_ticker] = QFDataFrame(df)
                    else:
                        self.logger.info(f"Not all tickers belong to family {future_ticker}")

                except Exception:
                    self.logger.debug(f"File {path} does not contain valid expiration dates and therefore will be "
                                      f"excluded.")

        # Log all the future tickers, which could not have been mapped correctly
        tickers_without_matching_files = set(future_tickers).difference(tickers_dates_dict.keys())
        for ticker in tickers_without_matching_files:
            tickers_dates_dict[ticker] = QFDataFrame(columns=[ExpirationDateField.LastTradeableDate])
            self.logger.warning(f"No expiration dates were found for ticker {ticker}. Check if file "
                                f"{ticker.family_id.replace('{}', '')}.txt exists in the {dir_path} and if it contains"
                                f"valid expiration dates for the ticker.")

        return tickers_dates_dict

    def _get_price_and_contracts(self, path: str, tickers: Sequence[Ticker], fields: Sequence[PriceField],
                                 start_date: datetime, end_date: datetime, freq: Frequency):

        field_to_price_field_dict = {
            'Open': PriceField.Open,
            'High': PriceField.High,
            'Low': PriceField.Low,
            'Close': PriceField.Close,
            'LastPrice': PriceField.Close,
            'Date': 'dates',
            'Date_Time': 'dates'
        }

        # it is required to distinguish intraday and daily volume
        if freq == Frequency.MIN_1:
            field_to_price_field_dict['TradeVolume'] = PriceField.Volume  # for intraday
        elif freq == Frequency.DAILY:
            field_to_price_field_dict['Volume'] = PriceField.Volume  # for daily

        tickers_strings_to_tickers = {
            ticker.as_string(): ticker for ticker in tickers if not isinstance(ticker, FutureTicker)
        }
        tickers_paths = [list(Path(path).glob('**/{}.csv'.format(ticker_str)))
                         for ticker_str in tickers_strings_to_tickers.keys()]
        joined_tickers_paths = [item for sublist in tickers_paths for item in sublist]

        tickers_prices_dict = {}
        contracts_data = {}

        for path in joined_tickers_paths:
            path = path.resolve()
            ticker_str = path.name.replace('.csv', '')
            ticker = tickers_strings_to_tickers[ticker_str]
            # It is important to save the Time and Date as strings, in order to correctly infer the date format
            df = QFDataFrame(pd.read_csv(path, dtype={"Time": str, "Date": str, "Date_Time": str}))

            if 'Time' in df and freq == Frequency.MIN_1:
                df.index = pd.to_datetime(df["Date"] + ' ' + df["Time"])
            elif 'Time' not in df and 'Date' in df and freq == Frequency.DAILY:
                df.index = pd.to_datetime(df['Date'])
            else:
                self.logger.info(f"Ticker {ticker} does not satisfy timing requirements. File path: {path}")
                continue

            contracts_data[ticker] = df['Contract'] if 'Contract' in df.columns else QFSeries()

            df = df.rename(columns=field_to_price_field_dict)
            df = df.loc[start_date:end_date, df.columns.isin(fields)]
            fields_diff = set(fields).difference(df.columns)
            if fields_diff:
                self.logger.info("Not all fields are available for {}. Difference: {}".format(ticker, fields_diff))

            tickers_prices_dict[ticker] = QFDataFrame(df)

        contracts_df = QFDataFrame(contracts_data)
        return tickers_dict_to_data_array(tickers_prices_dict, list(tickers_prices_dict.keys()), fields), contracts_df
