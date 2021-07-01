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
import pathlib
from os.path import join

from pandas import read_csv

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


def _acquire_data(input_file: str):
    data_frame = read_csv(input_file, parse_dates=['dates'])

    # The data_frame contains following headers: dates, open, high, low, close, volume, ticker.
    dates = data_frame['dates'].drop_duplicates()
    tickers = [DummyTicker(t) for t in data_frame['tickers'].unique()]

    # The columns in the csv file are in the exactly same order as the corresponding fields in the list below
    fields = PriceField.ohlcv()

    # Create a data array
    data_array = data_frame.set_index(['dates', 'tickers']).stack().to_xarray()

    # Construct a QFDataArray based on the data_array and sort it by the 'dates' coordinate
    data = QFDataArray.create(
        dates=dates,
        tickers=tickers,
        fields=fields,
        data=data_array
    ).sortby('dates')

    start_date = dates.iloc[0]
    end_date = dates.iloc[-1]

    return data, start_date, end_date


def _get_demo_data_provider(frequency: Frequency):

    frequency_to_data_file = {
        Frequency.MIN_1: "intraday_data.csv",
        Frequency.DAILY: "daily_data.csv"
    }

    input_file = join(pathlib.Path(__file__).parent.absolute(), "input", frequency_to_data_file[frequency])
    data, start_date, end_date = _acquire_data(input_file)
    return PresetDataProvider(data, start_date, end_date, frequency)


daily_data_provider = _get_demo_data_provider(Frequency.DAILY)
intraday_data_provider = _get_demo_data_provider(Frequency.MIN_1)
