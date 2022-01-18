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

""" PortaraDataProvider Demo

This module demonstrates the most important functionality of the Portara data provider. It provides examples on how to
download price data for individual or continuous contracts.

These examples may be run using the sample Portara data, which is available at https://www.portaracqg.com/sample-data/.

It is important to save the price data as csv, in order to not confuse the pricing data files with the files containing
expiration dates.
"""

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import PortaraTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.portara.portara_data_provider import PortaraDataProvider

pd.options.display.max_rows = 1000
pd.options.display.max_columns = 100


def daily_data_example(path_to_data_files: str):
    """
    In order to run the example you need to provide the path to the top directory, containing your data files. The
    example below will download Open, High, Low and Close Prices along with daily Volume for the E-mini S&P,
    EP2018M contract.

    Notes
    ---------
    The file containing data for the ticker should have the same name as the ticker that you are passing as the
    parameter. For example if you want to run this example for EP2018M, you should name your data file "EP2018M.csv"
    and download the prices using PortaraTicker("EP2018M").

    Parameters
    -----------
    path_to_data_files: str
        path to the top directory, which contains all your Portara data files
    """

    start_date = str_to_date('2018-02-26')
    end_date = str_to_date('2018-06-15')
    fields = PriceField.ohlcv()
    ticker = PortaraTicker('EP2018M', SecurityType.FUTURE, 50)
    daily_freq = Frequency.DAILY

    if path_to_data_files is None:
        raise ValueError("Please provide a correct path to the Portara data and assign it to the "
                         "path_to_data_files variable.")

    print('\nSingle ticker, daily frequency')
    dp = PortaraDataProvider(path_to_data_files, ticker, fields, start_date, end_date, daily_freq)
    prices = dp.get_price(ticker, fields, start_date, end_date, daily_freq)
    print(prices)


def intraday_data_example(path_to_data_files: str):
    """
    In order to run the example you need to provide the path to the top directory, containing your data files. The
    example below will download Open, High, Low and Close Prices along with Volume for the Japanese
    Government Bonds, JGB2019H contract, for the 1-minute bars frequency.

    Notes
    ---------
    The file containing data for the ticker should have the same name as the ticker that you are passing as the
    parameter. For example if you want to run this example for EP2018M, you should name your data file "JGB2019H.csv"
    and download the prices using PortaraTicker("JGB2019H").

    Parameters
    -----------
    path_to_data_files: str
        path to the top directory, which contains all your Portara data files
    """

    start_date = str_to_date('2019-02-22 00:00:00.0', DateFormat.FULL_ISO)
    end_date = str_to_date('2019-02-22 00:09:00.0', DateFormat.FULL_ISO)
    fields = PriceField.ohlcv()
    ticker = PortaraTicker('JGB2019H', SecurityType.FUTURE, 1000000)
    intraday_frequency = Frequency.MIN_1

    if path_to_data_files is None:
        raise ValueError("Please provide a correct path to the Portara data and assign it to the "
                         "path_to_data_files variable.")

    print('\nSingle ticker, 1-minute frequency')
    dp = PortaraDataProvider(path_to_data_files, ticker, fields, start_date, end_date, intraday_frequency)
    prices = dp.get_price(ticker, fields, start_date, end_date, intraday_frequency)
    print(prices)

    print('\nSingle ticker, 5-minute frequency')
    prices = dp.get_price(ticker, fields, start_date, end_date, Frequency.MIN_5)
    print(prices)


def continuous_contracts(path_to_data_files: str):
    """
    In order to run the example you need to provide the path to the top directory, containing your data files. The
    example below will download Open, High, Low and Close Prices along with Volume for the VIX Future CBOEFE and
    (Zero Adjust) and Johannesburg Wheat (Back Adjust) continuous contracts.

    Notes
    ---------
    The two files containing data for the ticker should have the same name as the tickers that you are passing as the
    parameter. For example - to run the example below, you will need to save prices of the data as VX.csv and WEAT.csv.

    Parameters
    -----------
    path_to_data_files: str
        path to the top directory, which contains all your Portara data files
    """

    start_date = str_to_date('2019-01-01')
    end_date = str_to_date('2019-01-10')
    fields = PriceField.ohlcv()
    tickers = [PortaraTicker("VX", SecurityType.FUTURE, 1000), PortaraTicker("WEAT", SecurityType.FUTURE, 100)]
    daily_freq = Frequency.DAILY

    if path_to_data_files is None:
        raise ValueError("Please provide a correct path to the Portara data and assign it to the "
                         "path_to_data_files variable.")

    print('\nMultiple continuous tickers, daily frequency, open prices')
    dp = PortaraDataProvider(path_to_data_files, tickers, fields, start_date, end_date, daily_freq)
    prices = dp.get_price(tickers, PriceField.Open, start_date, end_date, daily_freq)
    print(prices)

    print('\nMultiple continuous tickers, daily frequency, close prices')
    dp = PortaraDataProvider(path_to_data_files, tickers, fields, start_date, end_date, daily_freq)
    prices = dp.get_price(tickers, PriceField.Close, start_date, end_date, daily_freq)
    print(prices)


if __name__ == '__main__':
    # Download the sample data, adjust the files to the described naming convention (ticker_name.csv for each ticker)
    # and assign the path to the directory with your files to the path_to_data_files variable
    path_to_data_files = None

    daily_data_example(path_to_data_files)
    intraday_data_example(path_to_data_files)
    continuous_contracts(path_to_data_files)
