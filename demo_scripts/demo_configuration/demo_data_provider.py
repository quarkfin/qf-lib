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
from demo_scripts.common.utils.dummy_ticker import DummyTicker
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.data_providers.csv.csv_data_provider import CSVDataProvider

daily_data_path = join(pathlib.Path(__file__).parent.absolute(), "input", "daily_data.csv")
intraday_data_path = join(pathlib.Path(__file__).parent.absolute(), "input", "intraday_data.csv")


tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC'),
           DummyTicker('DDD'), DummyTicker('EEE'), DummyTicker('FFF')]

field_to_price_field_dict = {
            'open': PriceField.Open,
            'high': PriceField.High,
            'low': PriceField.Low,
            'close': PriceField.Close,
            'volume': PriceField.Volume,
        }

fields = ['open', 'high', 'low', 'close', 'volume']

daily_data_provider = CSVDataProvider(daily_data_path, tickers, 'dates', field_to_price_field_dict,
                                      fields, ticker_col='tickers')

intraday_data_provider = CSVDataProvider(intraday_data_path, tickers, 'dates', field_to_price_field_dict,
                                         fields, frequency=Frequency.MIN_1, ticker_col='tickers')
