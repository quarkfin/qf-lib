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

""" PortaraFutureTicker Demo

This module demonstrates the most important functionality of the Portara future tickers.

In order to run the examples, the following files are necessary:
- a .txt file containing expiration dates of individual contracts (name of the file should match the family_id, in the
example below family_id is set to "SIA{}" and the name of file with expiration dates is "SIA.txt")
- .csv files with pricing data for individual Silver contracts (SIA2021H.csv, SIA2021K.csv, SIA2021N.csv etc).
"""

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import PortaraTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.futures.future_tickers.portara_future_ticker import PortaraFutureTicker
from qf_lib.data_providers.portara.portara_data_provider import PortaraDataProvider


pd.options.display.max_rows = 1000
pd.options.display.max_columns = 100


def future_ticker_example(path_to_data_files: str):
    """
    In order to run the example you need to provide the path to the top directory, containing your data files. The
    example below will:

    1. initialize the Silver FutureTicker
    2. return the list of tickers belonging to the futures chain
    3. return the current specific ticker
    4. check for some tickers, if they belong to the Silver futures family
    5. return Open, High, Low, Close and Volume pricing data for the current specific ticker

    Parameters
    -----------
    path_to_data_files: str
        path to the top directory, which contains all your Portara data files
    """

    start_date = str_to_date('2020-12-02')
    end_date = str_to_date('2021-02-01')
    fields = PriceField.ohlcv()
    # Use the front contract (N = 1)
    # Roll the tickers 1 day before the expiration (days_before_exp_date = 1)
    # Set the point value to 50 (value for each of the contracts can be checked in Portara)
    future_ticker = PortaraFutureTicker('Silver', 'SIA{}', 1, 1, 50, designated_contracts="HKNUZ")
    daily_freq = Frequency.DAILY

    if path_to_data_files is None:
        raise ValueError("Please provide a correct path to the Portara data and assign it to the "
                         "path_to_data_files variable.")

    dp = PortaraDataProvider(path_to_data_files, future_ticker, fields, start_date, end_date, daily_freq)

    # Initialize the future ticker with the data provider and timer. Timer is used to identify the current front ticker.
    timer = SettableTimer()
    future_ticker.initialize_data_provider(timer, dp)

    print('\nCurrent individual contract (front contract) as of 10th December 2020:')
    timer.set_current_time(str_to_date('2020-12-10'))
    current_ticker = future_ticker.get_current_specific_ticker()
    print(f'> {current_ticker}')

    print('\nCurrent individual contract (front contract) as of 10th January 2021:')
    timer.set_current_time(str_to_date('2021-01-10'))
    current_ticker = future_ticker.get_current_specific_ticker()
    print(f'> {current_ticker}')

    print('\nCheck if the following tickers belong to the Silver futures chain:')
    ticker = PortaraTicker('SIA2017H', SecurityType.FUTURE, 50)
    print(f'- {ticker}: {future_ticker.belongs_to_family(ticker)}')
    ticker = PortaraTicker('OH2017H', SecurityType.FUTURE, 50)
    print(f'- {ticker}: {future_ticker.belongs_to_family(ticker)}')
    ticker = PortaraTicker('SIA2017', SecurityType.FUTURE, 50)
    print(f'- {ticker}: {future_ticker.belongs_to_family(ticker)}')
    ticker = PortaraTicker('SIA1999Z', SecurityType.FUTURE, 50)
    print(f'- {ticker}: {future_ticker.belongs_to_family(ticker)}')

    print('\nOpen, High, Low, Close and Volume pricing data for the current specific ticker (as of 10th January 2021)')
    prices = dp.get_price(current_ticker, PriceField.ohlcv(), start_date, end_date, daily_freq)
    print(prices)


if __name__ == '__main__':
    # Download the sample data, adjust the files to the described naming convention (ticker_name.csv for each ticker)
    # and assign the path to the directory with your files to the path_to_data_files variable
    path_to_data_files = None

    future_ticker_example(path_to_data_files)
